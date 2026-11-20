"""Prints the task markers received on LSL, with their time: checks that the task publishes them. Ctrl+C stops."""

from pylsl import StreamInlet, resolve_byprop

from cop import config


def main():
    print(f"Waiting for the LSL stream {config.MARKER_STREAM_NAME} (start scripts/run_center_out.py)...")
    inlet = StreamInlet(resolve_byprop("name", config.MARKER_STREAM_NAME)[0])
    print("Connected: markers sent from now on are printed.")
    try:
        while True:
            sample, time_s = inlet.pull_sample()
            print(f"{time_s:12.3f}  {sample[0]}")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()