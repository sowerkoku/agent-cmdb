# agent-cmdb Acceptance Test Suite
# Knowledge Kernel — validación funcional
#
# Cada consulta debe poder responderse SIN usar LLM ni memoria de Hermes.
# La respuesta viene de los hechos almacenados en el CMDB.
#
# Run: python3 -m pytest tests/acceptance/

import pytest
from pathlib import Path
import sys

# Add cmdb to path
sys.path.insert(0, str(Path.home() / "agent-cmdb"))

from cmdb.api import (
    cmdb_get, cmdb_exists, cmdb_search, cmdb_list,
    cmdb_impact, cmdb_validate, cmdb_context,
)


# =============================================================================
# INFRAESTRUCTURA
# ¿Dónde corre X? ¿Qué depende de Y? ¿Qué software está en Z?
# =============================================================================

class TestInfraestructura:
    """Pertenece: sí — hecho objetivo, única fuente de verdad, cambia poco."""
    
    def test_donde_corre_metabase(self):
        """¿Dónde corre Metabase?"""
        # Metabase corre en device-54
        result = cmdb_search("metabase")
        assert len(result) > 0, "Metabase no encontrado"
        
        metabase_id = result[0]["id"]
        entity = cmdb_get(metabase_id)
        assert entity.exists
        
        # Buscar runs_on en relations
        # (requiere que relations esté parseado correctamente)
        pass  # Validar que existe relación con host
    
    def test_que_depende_de_firebird(self):
        """¿Qué depende de Firebird?"""
        result = cmdb_impact("firebird-server")
        assert result["exists"]
        assert "depends_on_me" in result
        # Debe listar sync-bridge y cualquier otro que use Firebird
    
    def test_que_software_esta_en_device53(self):
        """¿Qué software está en device-53?"""
        result = cmdb_impact("device-53")
        assert result["exists"]
        # i_depend_on debería listar software que corre en este host
    
    def test_cual_es_el_estado_de_ollama(self):
        """¿Está Ollama operacional?"""
        result = cmdb_get("ollama")
        if result.exists:
            assert result.entity.status in ("operational", "degraded", "down")


# =============================================================================
# ORGANIZACIÓN
# ¿Qué proyectos/agentes/procedimientos existen?
# =============================================================================

class TestOrganizacion:
    """Pertenece: sí — hecho objetivo, múltiples agentes lo consultan."""
    
    def test_que_proyectos_existen(self):
        """¿Qué proyectos están registrados?"""
        # Buscar entidades tipo "project"
        results = cmdb_list(kind="projects")
        # O cmdb_search("project")
        pass
    
    def test_cual_es_el_objetivo_del_cic(self):
        """¿Cuál es el objetivo del CIC?"""
        entity = cmdb_get("cic")
        if entity.exists:
            # El objetivo debe estar en metadata.description
            assert "objective" in entity.entity.metadata or "description" in entity.entity.metadata
    
    def test_que_agentes_forman_el_sistema(self):
        """¿Qué agentes Hermes existen?"""
        # Buscar entidades tipo "agent" o kind="software" con tag "hermes"
        results = cmdb_search("hermes")
        # Filtrar por kind agent
    
    def test_quien_es_el_propietario_de_cada_proyecto(self):
        """¿Quién mantiene cada proyecto?"""
        # relations.should have "owned_by" or similar


# =============================================================================
# OPERACIÓN
# ¿Cómo se hace X? Procedimientos de operación estándar
# =============================================================================

class TestOperacion:
    """Pertenece: sí — conocimiento operativo factual."""
    
    def test_como_se_reinicia_metabase(self):
        """¿Cuál es el procedimiento para reiniciar Metabase?"""
        result = cmdb_get("metabase")
        if result.exists:
            # Buscar procedimiento asociado en relations
            # O buscar entidad procedimiento separada
            pass
    
    def test_como_se_valida_el_etl(self):
        """¿Cómo se valida el pipeline de ETL?"""
        result = cmdb_search("etl")
        result = cmdb_search("sync")
        # Debe devolver sync-bridge y su procedimiento asociado
    
    def test_como_se_recupera_firebird(self):
        """¿Cuál es el procedimiento de recuperación de Firebird?"""
        # Buscar entidad tipo "procedure" relacionada con firebird


# =============================================================================
# GOBERNANZA
# Políticas vigentes, decisiones activas
# =============================================================================

class TestGobernanza:
    """Pertenece: sí — decisiones que deben consultarse, no razonarse."""
    
    def test_cual_es_la_politica_de_margen_minimo(self):
        """¿Cuál es el margen mínimo permitido?"""
        # Buscar entidad "margin-policy" o similar
        result = cmdb_search("margin")
    
    def test_que_decisiones_estrategicas_siguen_vigentes(self):
        """¿Qué decisiones de arquitectura siguen vigentes?"""
        # Buscar entidades tipo "decision" con status="active" o "approved"
    
    def test_cual_es_el_contrato_de_niveles_sla(self):
        """¿Qué SLA tiene cada servicio?"""
        # Buscar entidades con metadata.sla


# =============================================================================
# RELACIONES Y DEPENDENCIAS
# ¿Qué se rompe si X falla? ¿Qué proyectos usan Y?
# =============================================================================

class TestRelaciones:
    """Pertenece: sí — impact analysis es的核心功能."""
    
    def test_que_se_rompe_si_device53_falla(self):
        """¿Qué servicios se afectan si device-53 cae?"""
        result = cmdb_impact("device-53")
        assert result["exists"]
        assert "depends_on_me" in result
        # Debe listar todos los dependientes directos y transitivos
    
    def test_que_proyectos_usan_metabase(self):
        """¿Qué proyectos dependen de Metabase?"""
        result = cmdb_impact("metabase")
        # affected_layers["projects"] debería tener los proyectos
    
    def test_hay_puntos_simples_de_falla(self):
        """¿Qué componentes son SPOF?"""
        # Para cada servicio crítico, cmdb_impact debe detectar SPOF
        result = cmdb_impact("firebird-server")
        if result["risk_indicators"]["total_dependents"] > 0:
            assert "single_point_of_failure" in result["risk_indicators"]
    
    def test_cual_es_la_cadena_de_dependencias_completa(self):
        """¿Cuál es el grafo completo de dependencias?"""
        # Dejar claro que runs_on es 1-hop
        # y depends_on es transitivo (BFS)


# =============================================================================
# CAPABILITIES
# ¿Qué puede hacer cada componente?
# =============================================================================

class TestCapabilities:
    """Pertenece: sí — capacidades son hechos objetivos."""
    
    def test_que_servicios_expone_cada_host(self):
        """¿Qué servicios están disponibles en cada host?"""
        # cmdb_context para el host debe listar services
        pass
    
    def test_que_herramientas_usan_los_agentes(self):
        """¿Qué herramientas usa cada agente?"""
        # cmdb_context del agente debe listar uses[]
        ctx = cmdb_context("hermes-arquitectobi")
        assert "known_environment" in ctx


# =============================================================================
# VALIDACIÓN DE INTEGRIDAD
# El sistema debe poder confiar en sus propios datos
# =============================================================================

class TestIntegridad:
    """Validaciones de salud del CMDB."""
    
    def test_cmdb_validate_pasa(self):
        """¿El CMDB está válido?"""
        result = cmdb_validate()
        assert result["valid"], f"Errores: {result['errors']}"
    
    def test_todas_las_entidades_tienen_id(self):
        """¿Todas las entidades tienen ID único?"""
        entities = cmdb_list()
        ids = [e["id"] for e in entities]
        assert len(ids) == len(set(ids)), "IDs duplicados encontrados"
    
    def test_entidades_contradictorias(self):
        """¿Hay entidades con estados contradictorios?"""
        # software con status=down pero sus dependientes operational
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])