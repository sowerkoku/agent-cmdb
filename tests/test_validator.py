"""
Tests for CMDB Validator

Run: cd ~/.hermes/profiles/arquitectobi/skill-registry && python3 -m pytest tests/test_validator.py -v
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from cmdb.validator import cmdb_validate, load_entities


def create_test_entity(entity_id: str, kind: str, **kwargs) -> dict:
    """Helper to create a valid test entity."""
    entity = {
        "schema_version": 1,
        "id": entity_id,
        "kind": kind,
        "metadata": {"name": f"Test {entity_id}"},
        "status": kwargs.get("status", "operational"),
        "relations": kwargs.get("relations", []),
    }
    
    if "criticality" in kwargs:
        entity["criticality"] = kwargs["criticality"]
    
    return entity


def write_entity(tmpdir: Path, entity: dict) -> Path:
    """Write entity to a YAML file."""
    filepath = tmpdir / f"{entity['id']}.yaml"
    with open(filepath, "w") as f:
        yaml.dump(entity, f)
    return filepath


class TestValidEntity:
    """Test validation of valid entities."""
    
    def test_valid_entity(self):
        """A valid entity should pass validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            entity = create_test_entity("mysql", "software", relations=[
                {"type": "runs_on", "target": "server-54"},
            ])
            write_entity(tmpdir, entity)
            
            # Also create the target entity
            server = create_test_entity("server-54", "asset")
            write_entity(tmpdir, server)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is True
            assert len(result["errors"]) == 0
    
    def test_valid_entity_with_criticality(self):
        """Entity with complete criticality should pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            entity = create_test_entity("mysql", "software", 
                criticality={
                    "business": "high",
                    "operational": "high",
                    "technical": "medium",
                },
                relations=[
                    {"type": "runs_on", "target": "server-54"},
                ]
            )
            write_entity(tmpdir, entity)
            
            server = create_test_entity("server-54", "asset")
            write_entity(tmpdir, server)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is True
            assert len(result["errors"]) == 0


class TestSchemaValidation:
    """Test schema validation rules."""
    
    def test_missing_schema_version(self):
        """Entity without schema_version should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            entity = {
                "id": "mysql",
                "kind": "software",
                "metadata": {"name": "MySQL"},
                "status": "operational",
            }
            write_entity(tmpdir, entity)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is False
            assert any(e["field"] == "schema_version" for e in result["errors"])
    
    def test_invalid_kind(self):
        """Entity with unknown kind should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            entity = create_test_entity("mysql", "unknown_kind")
            write_entity(tmpdir, entity)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is False
            assert any(e["field"] == "kind" for e in result["errors"])


class TestIdentityValidation:
    """Test identity validation rules."""
    
    def test_duplicate_id(self):
        """Duplicate IDs should fail validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create subdirectories to avoid filename collision
            subdir1 = tmpdir / "subdir1"
            subdir2 = tmpdir / "subdir2"
            subdir1.mkdir()
            subdir2.mkdir()
            
            entity1 = create_test_entity("mysql", "software")
            entity2 = create_test_entity("mysql", "software")  # Same ID
            
            write_entity(subdir1, entity1)
            write_entity(subdir2, entity2)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is False
            assert any("Duplicate ID" in e["message"] for e in result["errors"])
    
    def test_invalid_id_format(self):
        """Invalid ID format should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            entity = create_test_entity("MySQL_Server", "software")  # Invalid: uppercase, underscore
            write_entity(tmpdir, entity)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is False
            assert any(e["field"] == "id" and "Invalid ID format" in e["message"] for e in result["errors"])


class TestRelationValidation:
    """Test relation validation rules."""
    
    def test_missing_relation_target(self):
        """Relation with non-existent target should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            entity = create_test_entity("mysql", "software", relations=[
                {"type": "runs_on", "target": "nonexistent-server"},
            ])
            write_entity(tmpdir, entity)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is False
            assert any("does not exist" in e["message"] for e in result["errors"])
    
    def test_invalid_relation_type(self):
        """Unknown relation type should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            entity = create_test_entity("mysql", "software", relations=[
                {"type": "depends_on", "target": "server-54"},  # Invalid type
            ])
            write_entity(tmpdir, entity)
            
            server = create_test_entity("server-54", "asset")
            write_entity(tmpdir, server)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is False
            assert any("Unknown relation type" in e["message"] for e in result["errors"])
    
    def test_runs_on_wrong_target_kind(self):
        """runs_on must point to an asset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            entity = create_test_entity("mysql", "software", relations=[
                {"type": "runs_on", "target": "postgres"},  # postgres is software, not asset
            ])
            write_entity(tmpdir, entity)
            
            postgres = create_test_entity("postgres", "software")
            write_entity(tmpdir, postgres)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is False
            assert any("requires target kind" in e["message"] for e in result["errors"])


class TestLifecycleValidation:
    """Test lifecycle validation rules."""
    
    def test_deprecated_dependency_warning(self):
        """Depending on deprecated entity should warn (not error)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            entity = create_test_entity("app", "software", relations=[
                {"type": "uses", "target": "old-lib"},
            ])
            write_entity(tmpdir, entity)
            
            old_lib = create_test_entity("old-lib", "software", status="deprecated")
            write_entity(tmpdir, old_lib)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is True  # Warnings don't block
            assert len(result["warnings"]) > 0
            assert any("deprecated" in w["message"] for w in result["warnings"])
    
    def test_software_without_runs_on_warning(self):
        """Software without runs_on should warn."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            entity = create_test_entity("mysql", "software", relations=[])
            write_entity(tmpdir, entity)
            
            result = cmdb_validate(tmpdir)
            
            assert result["valid"] is True
            assert any("runs_on" in w["message"] for w in result["warnings"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])