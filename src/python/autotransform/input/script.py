                replaced_cmd,
                capture_output=True,
                encoding="utf-8",
                timeout=self.timeout,
            )
            stdout_message = f"STDOUT:
            stderr_message = f"STDERR:
            event_handler.handle(VerboseEvent({"message": stdout_message}))
            event_handler.handle(VerboseEvent({"message": stderr_message}))
            proc.check_returncode()
            if uses_result_file:
                with open(result_file.name, encoding="utf-8") as results:
                    item_data = json.loads(results.read())
            else:
                item_data = json.loads(proc.stdout.strip())
        return [item_factory.get_instance(item) for item in item_data]