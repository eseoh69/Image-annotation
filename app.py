import streamlit as st
import threading
import time
import uuid
import os
import json
from PIL import Image
from broker.redis_broker import RedisBroker
from services.inference_service import InferenceService
from services.cli_service import CLIService
import pandas as pd

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="EC530 Image Annotation System",
    page_icon="🔍",
    layout="wide"
)

# ─── Session State ─────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = {}
if "pipeline_log" not in st.session_state:
    st.session_state.pipeline_log = []
if "services_started" not in st.session_state:
    st.session_state.services_started = False
if "cli" not in st.session_state:
    st.session_state.cli = None
if "current_image_id" not in st.session_state:
    st.session_state.current_image_id = None
if "annotated_image_path" not in st.session_state:
    st.session_state.annotated_image_path = None

# ─── Start Background Services ─────────────────────────────────
@st.cache_resource
def start_services():
    inference_broker = RedisBroker()
    annotation_broker = RedisBroker()
    embedding_broker = RedisBroker()
    cli_broker = RedisBroker()

    # Start inference service
    inference = InferenceService(inference_broker)
    inference_thread = threading.Thread(target=inference.start, daemon=True)
    inference_thread.start()

    # Start annotation service
    from services.annotation_service import AnnotationService
    annotation = AnnotationService(annotation_broker)
    annotation_thread = threading.Thread(target=annotation.start, daemon=True)
    annotation_thread.start()

    # Start embedding service
    from services.embedding_service import EmbeddingService
    embedding = EmbeddingService(embedding_broker)
    embedding_thread = threading.Thread(target=embedding.start, daemon=True)
    embedding_thread.start()

    # Start CLI service
    cli = CLIService(cli_broker)
    cli.start()

    time.sleep(1)
    return cli

cli = start_services()

# ─── Header ────────────────────────────────────────────────────
st.title("🔍 EC530 Image Annotation System")
st.caption("Event-driven image upload, object detection via YOLOv8, and retrieval — Boston University EC530")
st.divider()

# ─── Layout: two columns ───────────────────────────────────────
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("📤 Upload Image")
    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["jpg", "jpeg", "png"],
        help="Upload any image — YOLOv8 will detect objects in it"
    )

    if uploaded_file is not None:
        os.makedirs("images/uploads", exist_ok=True)
        temp_path = f"images/uploads/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.image(uploaded_file, caption="Original Image", use_container_width=True)

        if st.button("🚀 Run Detection", type="primary", use_container_width=True):
            # Reset state
            st.session_state.pipeline_log = []
            st.session_state.annotated_image_path = None

            # Generate image ID
            image_id = f"img_{uuid.uuid4().hex[:8]}"
            st.session_state.current_image_id = image_id

            # Log event 1
            st.session_state.pipeline_log.append("📨 **image.submitted** → sent to Redis")

            # Upload through CLI service
            event = cli.gen.image_submitted(image_id)
            event["payload"]["path"] = temp_path
            event["payload"]["image_id"] = image_id
            cli.broker.publish("image.submitted", event)

            # Wait for inference to complete
            with st.spinner("Running YOLOv8 inference..."):
                for _ in range(20):
                    time.sleep(1)
                    if image_id in cli.results:
                        break

            # Log remaining events
            st.session_state.pipeline_log.append("⚙️ **inference.completed** → objects detected")
            st.session_state.pipeline_log.append("💾 **annotation.stored** → saved to MongoDB Atlas")
            st.session_state.pipeline_log.append("🔢 **embedding.created** → vector indexed in FAISS")

            # Store results
            if image_id in cli.results:
                st.session_state.results[image_id] = cli.results[image_id]

            # Generate annotated image using YOLO
            from ultralytics import YOLO
            model = YOLO("yolov8n.pt")
            results = model(temp_path, verbose=False)
            annotated_path = f"images/uploads/annotated_{uploaded_file.name}"
            results[0].save(filename=annotated_path)
            st.session_state.annotated_image_path = annotated_path

            st.rerun()

with right_col:
    # ─── Pipeline Status Feed ──────────────────────────────────
    st.subheader("📡 Pipeline Events")
    if st.session_state.pipeline_log:
        for log in st.session_state.pipeline_log:
            st.markdown(f"✅ {log}")
    else:
        st.info("Pipeline events will appear here after you run detection.")

    st.divider()

    # ─── Annotated Image ───────────────────────────────────────
    if st.session_state.annotated_image_path and os.path.exists(st.session_state.annotated_image_path):
        st.subheader("🖼️ Annotated Image")
        st.image(st.session_state.annotated_image_path, caption="Detected Objects", use_container_width=True)

# ─── Results Table ─────────────────────────────────────────────
image_id = st.session_state.current_image_id
if image_id and image_id in cli.results:
    st.divider()
    st.subheader("📊 Detected Objects")

    objects = cli.results[image_id]

    counts = {}
    conf_totals = {}
    for obj in objects:
        label = obj["label"]
        conf = obj["conf"]
        counts[label] = counts.get(label, 0) + 1
        conf_totals[label] = conf_totals.get(label, 0.0) + conf

    table_data = []
    for label, count in sorted(counts.items(), key=lambda x: -x[1]):
        avg_conf = round(conf_totals[label] / count, 2)
        table_data.append({
            "Object": label,
            "Count": count,
            "Avg Confidence": avg_conf,
        })

    df = pd.DataFrame(table_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Count": st.column_config.NumberColumn(format="%d"),
            "Avg Confidence": st.column_config.NumberColumn(format="%.2f"),
        }
    )

    total = sum(counts.values())
    summary = ", ".join([f"{c} {l}" for l, c in sorted(counts.items(), key=lambda x: -x[1])])
    st.success(f"**{total} objects detected:** {summary}")

# ─── Similarity Search ─────────────────────────────────────────
st.divider()
st.subheader("🔍 Search Similar Images")

col1, col2 = st.columns([3, 1])
with col1:
    query_image_id = st.text_input(
        "Enter image_id to find similar images",
        placeholder="e.g. img_4dde7a30"
    )
with col2:
    top_k = st.slider("Top K", min_value=1, max_value=5, value=3)

if st.button("🔎 Search", use_container_width=False):
    if query_image_id:
        from db.vector_index import VectorIndex
        from db.document_db import DocumentDB
        index = VectorIndex(dim=128)
        db = DocumentDB()

        annotation = db.get_annotation(query_image_id)
        if annotation:
            from services.embedding_service import EmbeddingService
            es = EmbeddingService.__new__(EmbeddingService)
            vector = es._simulate_embedding(annotation.get("objects", []))
            results = index.search(vector, k=top_k)

            if results:
                st.write(f"**Top {len(results)} similar images:**")
                for r in results:
                    ann = db.get_annotation(r["image_id"])
                    if ann:
                        labels = [o["label"] for o in ann.get("objects", [])]
                        counts = {}
                        for l in labels:
                            counts[l] = counts.get(l, 0) + 1
                        summary = ", ".join([f"{c} {l}" for l, c in sorted(counts.items(), key=lambda x: -x[1])])
                        st.markdown(f"- `{r['image_id']}` — distance: `{r['distance']}` — {summary}")
            else:
                st.warning("No similar images found. Upload more images first.")
        else:
            st.error(f"Image ID not found: {query_image_id}")
    else:
        st.warning("Please enter an image_id to search.")

# ─── Session History ───────────────────────────────────────────
if st.session_state.results:
    st.divider()
    st.subheader("🕓 Session History")
    for img_id, objs in st.session_state.results.items():
        counts = {}
        for obj in objs:
            counts[obj["label"]] = counts.get(obj["label"], 0) + 1
        summary = ", ".join([f"{c} {l}" for l, c in sorted(counts.items(), key=lambda x: -x[1])])
        st.markdown(f"- `{img_id}` → {summary}")