import time
import threading
from broker.redis_broker import RedisBroker
from services.inference_service import InferenceService
from services.cli_service import CLIService

def main():
    # Two separate brokers — one for each service
    inference_broker = RedisBroker()
    cli_broker = RedisBroker()

    # Start inference service in background thread
    inference = InferenceService(inference_broker)
    inference_thread = threading.Thread(target=inference.start, daemon=True)
    inference_thread.start()

    # Start CLI service
    cli = CLIService(cli_broker)
    cli.start()

    # Give services time to connect
    time.sleep(1)

    print("\n🚀 EC530 Image Annotation System")
    print("Commands:")
    print("  upload <image_path>  — upload a real image")
    print("  query <image_id>     — query results for an image")
    print("  list                 — show all processed images")
    print("  quit                 — exit\n")

    while True:
        try:
            cmd = input("> ").strip().split()
            if not cmd:
                continue

            if cmd[0] == "upload" and len(cmd) == 2:
                image_id = cli.upload_image(cmd[1])
                if image_id:
                    print(f"[CLI] Processing... checking every 2 seconds (max 30s)...")
                    for _ in range(15):
                        time.sleep(2)
                        if image_id in cli.results:
                            cli.query(image_id)
                            break
                    else:
                        print(f"[CLI] Timed out. Try: query {image_id}")

            elif cmd[0] == "query" and len(cmd) == 2:
                cli.query(cmd[1])

            elif cmd[0] == "list":
                if cli.results:
                    print("\n[CLI] Processed images:")
                    for img_id in cli.results:
                        print(f"  - {img_id}")
                else:
                    print("[CLI] No images processed yet.")

            elif cmd[0] == "quit":
                print("Goodbye!")
                break

            else:
                print("Commands: upload <path> | query <image_id> | list | quit")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()