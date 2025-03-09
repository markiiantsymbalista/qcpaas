class WorkerMetadata:
    def __init__(self, url, supported_packages):
        self.url = url
        self.supported_packages = supported_packages

class WorkerMetadataRegister:
    def __init__(self):
        self.items = []

    def add_worker_metadata(self, url, supported_packages):
        item = WorkerMetadata(url, supported_packages)
        self.items.append(item)
    
    def get_worker_by_supported_packages(self, search_packages):
        for item in self.items:
            if all(pkg in item.supported_packages for pkg in search_packages):
                return item
        return None  