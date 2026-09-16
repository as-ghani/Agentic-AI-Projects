from app import build_app


def main() -> None:
    app = build_app()
    assert app is not None
    print("Blocks constructed successfully")


if __name__ == "__main__":
    main()
