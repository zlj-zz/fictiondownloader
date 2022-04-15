try:
    import uvicorn
except ModuleNotFoundError:
    print("Use 'pip install uvicorn[standard]' to install uvicorn first.")
    exit(1)


def api_run():
    uvicorn.run(app="noval.api.main:app", port=9111, reload=True)


if __name__ == "__main__":
    api_run()
