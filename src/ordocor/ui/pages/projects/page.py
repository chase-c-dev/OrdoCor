from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ordocor.data.database import Database

from .dialog import ProjectDialog


PROJECT_ID_ROLE = Qt.UserRole + 1


class ProjectsPage(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self._build_ui()
        self._load_projects()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        heading = QLabel("Projects")
        heading.setStyleSheet("color: #F3E7C9; font-size: 28px; font-weight: 800;")

        panel = QFrame()
        panel.setObjectName("projectsPanel")
        panel.setStyleSheet(
            """
            QFrame#projectsPanel {
                background: #231C20;
                border: 1px solid #665451;
                border-radius: 8px;
            }
            """
        )
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Current Projects")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self._add_project)
        modify_button.clicked.connect(self._modify_project)
        remove_button.clicked.connect(self._remove_project)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(modify_button)
        header.addWidget(remove_button)

        self.projects_table = QTableWidget(0, 2)
        self.projects_table.setHorizontalHeaderLabels(("Project", "Description"))
        self.projects_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.projects_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.projects_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.projects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.projects_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.projects_table.verticalHeader().setVisible(False)
        self.projects_table.doubleClicked.connect(self._modify_project)

        hint = QLabel("Double-click a project to edit the full description.")
        hint.setStyleSheet("color: #B6A896; font-size: 12px;")

        panel_layout.addLayout(header)
        panel_layout.addWidget(hint)
        panel_layout.addWidget(self.projects_table, stretch=1)

        layout.addWidget(heading)
        layout.addWidget(panel, stretch=1)

    def _load_projects(self) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, description
                FROM projects
                ORDER BY name, id
                """
            ).fetchall()

        self.projects_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.projects_table.insertRow(row_index)
            values = (row["name"] or "", self._preview(row["description"] or ""))
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(PROJECT_ID_ROLE, row["id"])
                self.projects_table.setItem(row_index, column, item)

    def _add_project(self) -> None:
        dialog = ProjectDialog(self, "Add Project")
        if dialog.exec() != QDialog.Accepted:
            return

        project = dialog.project_data()
        if not self._validate_project(project):
            return

        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO projects (name, description) VALUES (?, ?)",
                (project["name"], project["description"]),
            )
        self._load_projects()

    def _modify_project(self) -> None:
        project_id = self._selected_project_id()
        if project_id is None:
            return

        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, name, description FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()

        if row is None:
            return

        dialog = ProjectDialog(self, "Modify Project", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return

        project = dialog.project_data()
        if not self._validate_project(project):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE projects
                SET name = ?,
                    description = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (project["name"], project["description"], project_id),
            )
        self._load_projects()

    def _remove_project(self) -> None:
        project_id = self._selected_project_id()
        if project_id is None:
            return

        with self.database.connect() as connection:
            connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self._load_projects()

    def _selected_project_id(self) -> int | None:
        selected_items = self.projects_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self.projects_table.item(row, 0)
        return item.data(PROJECT_ID_ROLE) if item else None

    def _validate_project(self, project: dict[str, str]) -> bool:
        if not project["name"]:
            QMessageBox.warning(self, "Missing Project Name", "Project name is required.")
            return False
        return True

    def _preview(self, description: str) -> str:
        collapsed = " ".join(description.split())
        return collapsed[:140] + "..." if len(collapsed) > 140 else collapsed
