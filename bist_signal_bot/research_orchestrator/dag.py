from bist_signal_bot.research_orchestrator.models import ResearchTask, ResearchDependency, ResearchRunPlan

class ResearchDAGBuilder:
    def topological_sort(self, tasks: list[ResearchTask], dependencies: list[ResearchDependency]) -> list[ResearchTask]:
        in_degree = {t.task_id: 0 for t in tasks}
        adj = {t.task_id: [] for t in tasks}
        task_map = {t.task_id: t for t in tasks}

        # Use explicitly defined dependencies
        for dep in dependencies:
            if dep.from_task_id in in_degree and dep.to_task_id in in_degree:
                adj[dep.from_task_id].append(dep.to_task_id)
                in_degree[dep.to_task_id] += 1

        queue = [t_id for t_id, deg in in_degree.items() if deg == 0]
        # Sort queue to make it deterministic
        queue.sort()

        sorted_tasks = []
        while queue:
            curr = queue.pop(0)
            sorted_tasks.append(task_map[curr])

            next_nodes = adj[curr]
            next_nodes.sort()
            for neighbor in next_nodes:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return sorted_tasks

    def detect_cycles(self, tasks: list[ResearchTask], dependencies: list[ResearchDependency]) -> list[str]:
        # Simple cycle detection using DFS
        adj = {t.task_id: [] for t in tasks}
        for dep in dependencies:
            if dep.from_task_id in adj and dep.to_task_id in adj:
                adj[dep.from_task_id].append(dep.to_task_id)

        visited = set()
        rec_stack = set()
        cycle_nodes = []

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        cycle_nodes.append(neighbor)
                        return True
                elif neighbor in rec_stack:
                    cycle_nodes.append(neighbor)
                    return True
            rec_stack.remove(node)
            return False

        for task in tasks:
            if task.task_id not in visited:
                if dfs(task.task_id):
                    cycle_nodes.append(task.task_id)
                    break

        return cycle_nodes

    def task_levels(self, tasks: list[ResearchTask], dependencies: list[ResearchDependency]) -> list[list[ResearchTask]]:
        # BFS level generation
        in_degree = {t.task_id: 0 for t in tasks}
        adj = {t.task_id: [] for t in tasks}
        task_map = {t.task_id: t for t in tasks}

        for dep in dependencies:
            if dep.from_task_id in in_degree and dep.to_task_id in in_degree:
                adj[dep.from_task_id].append(dep.to_task_id)
                in_degree[dep.to_task_id] += 1

        queue = [t_id for t_id, deg in in_degree.items() if deg == 0]
        queue.sort()

        levels = []
        while queue:
            level_tasks = [task_map[t_id] for t_id in queue]
            levels.append(level_tasks)
            next_queue = []
            for curr in queue:
                next_nodes = adj[curr]
                next_nodes.sort()
                for neighbor in next_nodes:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_queue.append(neighbor)
            queue = next_queue

        return levels

    def validate_dependencies(self, tasks: list[ResearchTask], dependencies: list[ResearchDependency]) -> list[str]:
        errors = []
        task_ids = {t.task_id for t in tasks}
        for dep in dependencies:
            if dep.from_task_id not in task_ids:
                errors.append(f"Dependency references unknown from_task_id: {dep.from_task_id}")
            if dep.to_task_id not in task_ids:
                errors.append(f"Dependency references unknown to_task_id: {dep.to_task_id}")

        cycles = self.detect_cycles(tasks, dependencies)
        if cycles:
            errors.append(f"DAG cycle detected involving nodes: {cycles}")

        return errors

    def render_mermaid(self, plan: ResearchRunPlan) -> str:
        lines = ["graph TD"]
        for task in plan.tasks:
            lines.append(f"    {task.task_id}[{task.name}]")
        for dep in plan.dependencies:
            lines.append(f"    {dep.from_task_id} --> {dep.to_task_id}")
        return "\n".join(lines)
