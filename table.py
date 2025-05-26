class Table:
    table_count = 0
    def __init__(self):
        Table.table_count += 1
        self.table_id = Table.table_count
        self.members = []

    def add_member(self, member: str):
        if member not in self.members:
            self.members.append(member)

    def __repr__(self):
        return f"Table(table_id={self.table_id})"

    def __str__(self):
        return f"Table ID: {self.table_id}"