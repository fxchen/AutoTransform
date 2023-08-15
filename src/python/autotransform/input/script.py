            event_handler.handle(VerboseEvent({"message": f"Running command: {replaced_cmd}"}))
            proc = subprocess.run(
                replaced_cmd,
                capture_output=True,
                encoding="utf-8",
                check=False,
                timeout=self.timeout,
            )
            proc.check_returncode()
            if uses_result_file:
                with open(result_file.name, encoding="utf-8") as results:
                    item_data = json.loads(results.read())
            else:
                item_data = json.loads(proc.stdout.strip())
        return [item_factory.get_instance(item) for item in item_data]