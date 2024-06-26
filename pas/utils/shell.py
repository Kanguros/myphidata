from pas.utils.log import logger


def run_shell_command(args: list[str], tail: int = 100) -> str:
    logger.info(f"Running shell command: {args}")

    import subprocess

    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        logger.debug(f"Result: {result}")
        logger.debug(f"Return code: {result.returncode}")
        if result.returncode != 0:
            return f"Error: {result.stderr}"

        # return only the last n lines of the output
        return "\n".join(result.stdout.split("\n")[-tail:])
    except Exception as e:
        logger.warning(f"Failed to run shell command: {e}")
        return f"Error: {e}"
