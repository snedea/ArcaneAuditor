"""Unit tests for GridPagingWithSortableFilterableRule."""

from parser.rules.structure.widgets.grid_paging_with_sortable_filterable import GridPagingWithSortableFilterableRule
from parser.models import PMDModel, PodModel, ProjectContext


class TestGridPagingWithSortableFilterableRule:
    """Test cases for GridPagingWithSortableFilterableRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = GridPagingWithSortableFilterableRule()
        assert rule.ID == "GridPagingWithSortableFilterableRule"
        assert rule.DESCRIPTION == "Detects grids with paging and sortableAndFilterable columns which can cause performance issues"
        assert rule.SEVERITY == "ACTION"

    def test_get_description(self):
        """Test that get_description returns the correct description."""
        rule = GridPagingWithSortableFilterableRule()
        assert rule.get_description() == rule.DESCRIPTION

    def test_grid_with_autopaging_and_sortable_filterable_column(self):
        """Test that grid with autoPaging and sortableAndFilterable column is flagged."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "grid",
                            "id": "workersGrid",
                            "autoPaging": True,
                            "columns": [
                                {
                                    "columnId": "workerName",
                                    "sortableAndFilterable": True
                                }
                            ]
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "workersGrid" in findings[0].message or "grid" in findings[0].message.lower()
        assert "paging" in findings[0].message.lower()
        assert "sortableAndFilterable" in findings[0].message
        assert findings[0].severity == "ACTION"

    def test_grid_with_paginginfo_and_sortable_filterable_column(self):
        """Test that grid with pagingInfo and sortableAndFilterable column is flagged."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "grid",
                            "id": "workersGrid",
                            "pagingInfo": {"pageSize": 50},
                            "columns": [
                                {
                                    "columnId": "workerName",
                                    "sortableAndFilterable": True
                                }
                            ]
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1

    def test_grid_with_paging_no_sortable_filterable(self):
        """Test that grid with paging but no sortableAndFilterable is not flagged."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "grid",
                            "id": "workersGrid",
                            "autoPaging": True,
                            "columns": [
                                {
                                    "columnId": "workerName",
                                    "sortableAndFilterable": False
                                }
                            ]
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_grid_without_paging_with_sortable_filterable(self):
        """Test that grid without paging but with sortableAndFilterable is not flagged."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "grid",
                            "id": "workersGrid",
                            "columns": [
                                {
                                    "columnId": "workerName",
                                    "sortableAndFilterable": True
                                }
                            ]
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_grid_with_paging_multiple_sortable_columns(self):
        """Test that grid with paging and multiple sortableAndFilterable columns shows multiple violations."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "grid",
                            "id": "workersGrid",
                            "autoPaging": True,
                            "columns": [
                                {
                                    "columnId": "workerName",
                                    "sortableAndFilterable": True
                                },
                                {
                                    "columnId": "department",
                                    "sortableAndFilterable": True
                                },
                                {
                                    "columnId": "email",
                                    "sortableAndFilterable": False
                                }
                            ]
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert any("workerName" in f.message for f in findings)
        assert any("department" in f.message for f in findings)

    def test_non_grid_widget_not_checked(self):
        """Test that non-grid widgets are not checked."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "text",
                            "id": "myText",
                            "autoPaging": True
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_pod_grid_with_paging_and_sortable(self):
        """Test that POD grids with paging and sortableAndFilterable are flagged."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pod_data = {
            "podId": "testPod",
            "file_path": "test.pod",
            "seed": {
                "template": {
                    "type": "grid",
                    "id": "myGrid",
                    "autoPaging": True,
                    "columns": [
                        {
                            "columnId": "name",
                            "sortableAndFilterable": True
                        }
                    ]
                }
            }
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"testPod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].file_path == "test.pod"

    def test_grid_without_columns_no_crash(self):
        """Test that grids without columns don't cause crashes."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "grid",
                            "id": "workersGrid",
                            "autoPaging": True
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_nested_grid_in_section(self):
        """Test that nested grids are properly detected."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "section",
                            "id": "mySection",
                            "children": [
                                {
                                    "type": "grid",
                                    "id": "nestedGrid",
                                    "autoPaging": True,
                                    "columns": [
                                        {
                                            "columnId": "data",
                                            "sortableAndFilterable": True
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1

    def test_autopaging_false_not_flagged(self):
        """Test that autoPaging: false is not treated as having paging."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "grid",
                            "id": "workersGrid",
                            "autoPaging": False,
                            "columns": [
                                {
                                    "columnId": "workerName",
                                    "sortableAndFilterable": True
                                }
                            ]
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_grid_in_tabs_with_paging_and_sortable(self):
        """Test that grid in tabs section with paging and sortableAndFilterable is flagged."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {},
                "tabs": [
                    {
                        "type": "section",
                        "children": [
                            {
                                "type": "grid",
                                "id": "workersGrid",
                                "autoPaging": True,
                                "columns": [
                                    {
                                        "columnId": "workerName",
                                        "sortableAndFilterable": True
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "workersGrid" in findings[0].message or "grid" in findings[0].message.lower()
        assert "paging" in findings[0].message.lower()
        assert "sortableAndFilterable" in findings[0].message

    def test_grid_in_multiple_tabs_analyzed(self):
        """Test that grids in multiple tabs are all analyzed."""
        rule = GridPagingWithSortableFilterableRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {},
                "tabs": [
                    {
                        "type": "section",
                        "children": [
                            {
                                "type": "grid",
                                "id": "grid1",
                                "autoPaging": True,
                                "columns": [
                                    {
                                        "columnId": "col1",
                                        "sortableAndFilterable": True
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "children": [
                            {
                                "type": "grid",
                                "id": "grid2",
                                "autoPaging": True,
                                "columns": [
                                    {
                                        "columnId": "col2",
                                        "sortableAndFilterable": True
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert any("grid1" in f.message or "col1" in f.message for f in findings)
        assert any("grid2" in f.message or "col2" in f.message for f in findings)

