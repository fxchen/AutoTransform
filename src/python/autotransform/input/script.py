            proc.check_returncode()
            if uses_result_file:
                with open(result_file.name, encoding="utf-8") as results:
            else:
                item_data = json.loads(proc.stdout.strip())
        return [item_factory.get_instance(item) for item in item_data]