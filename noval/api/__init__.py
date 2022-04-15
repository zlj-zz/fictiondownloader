import uvicorn


def api_run():
    uvicorn.run(app="noval.api.main:app", port=9111, reload=True)


if __name__ == "__main__":
    api_run()
