from typing import List, Dict
from bist_signal_bot.research_lab.models import ResearchJob
from bist_signal_bot.core.exceptions import ResearchJobDependencyError

class ResearchJobDependencyResolver:
    def build_graph(self, jobs: List[ResearchJob]) -> Dict[str, List[str]]:
        graph = {}
        for j in jobs:
            graph[j.job_id] = j.depends_on
        return graph

    def validate_graph(self, jobs: List[ResearchJob]) -> List[str]:
        errors = []
        job_ids = {j.job_id for j in jobs}

        for j in jobs:
            for dep in j.depends_on:
                if dep not in job_ids:
                    errors.append(f"Job {j.job_id} depends on missing job {dep}")
                if dep == j.job_id:
                    errors.append(f"Job {j.job_id} depends on itself")

        graph = self.build_graph(jobs)
        visited = set()
        path = set()

        def has_cycle(node):
            visited.add(node)
            path.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in path:
                    errors.append(f"Circular dependency detected involving {neighbor}")
                    return True
            path.remove(node)
            return False

        for node in graph:
            if node not in visited:
                has_cycle(node)
        return errors

    def ready_jobs(self, jobs: List[ResearchJob]) -> List[ResearchJob]:
        return [j for j in jobs if not j.depends_on]

    def topological_sort(self, jobs: List[ResearchJob]) -> List[ResearchJob]:
        if not jobs:
             return []
        errors = self.validate_graph(jobs)
        if errors:
            raise ResearchJobDependencyError(f"Cannot sort graph with errors: {errors}")

        graph = self.build_graph(jobs)
        visited = set()
        stack = []

        def dfs(node):
            visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
            stack.insert(0, node)

        for node in graph:
            if node not in visited:
                dfs(node)

        job_map = {j.job_id: j for j in jobs}
        sorted_ids = stack[::-1]
        return [job_map[jid] for jid in sorted_ids if jid in job_map]
