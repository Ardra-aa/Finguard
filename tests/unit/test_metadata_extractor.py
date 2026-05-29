"""PART 1 — Unit Tests: test_metadata_extractor.py + test_compliance_validator.py combined"""
import pytest
from Finguard_rag.ingestion.metadata_extractor import get_metadata, get_all_filenames


class TestMetadataExtractor:
    def test_get_metadata_returns_dict_for_known_file(self):
        filenames = get_all_filenames()
        if filenames:
            meta = get_metadata(filenames[0])
            assert meta is not None
            assert "doc_id" in meta

    def test_get_metadata_returns_none_for_unknown(self):
        meta = get_metadata("NONEXISTENT_FILE_XYZ.pdf")
        assert meta is None

    def test_metadata_has_required_keys(self):
        filenames = get_all_filenames()
        if filenames:
            meta = get_metadata(filenames[0])
            for key in ["doc_id", "jurisdiction", "regulatory_scope", "valid_roles",
                        "effective_date", "version", "risk_level", "risk_score"]:
                assert key in meta

    def test_metadata_jurisdiction_is_list(self):
        filenames = get_all_filenames()
        if filenames:
            meta = get_metadata(filenames[0])
            assert isinstance(meta["jurisdiction"], list)

    def test_get_all_filenames_returns_list(self):
        filenames = get_all_filenames()
        assert isinstance(filenames, list)
        assert len(filenames) > 0


# ── Compliance Validator ──────────────────────────────────────────────────
from Finguard_rag.generation.compliance_validator import validate
from datetime import date
from Finguard_rag.schemas.document_schema import UserContext, RankedDocument, FinancialDocument


def _ctx():
    return UserContext(
        user_id="t@t.com", role="compliance_officer", jurisdiction="IN",
        reference_date=date.today(), session_id="s1",
    )


class TestComplianceValidator:
    def test_mock_mode_returns_pass(self):
        result = validate("any text", [], _ctx(), mock_mode=True)
        assert result["status"] == "PASS"
        assert result["withheld"] is False

    def test_clean_text_passes(self):
        result = validate(
            "SEBI requires timely disclosure of material events.",
            [], _ctx(),
        )
        assert result["status"] in ("PASS", "WARNING")

    def test_violation_detected_on_bad_text(self):
        result = validate(
            "We recommend to buy shares during the trading window closure period.",
            [], _ctx(),
        )
        assert result["status"] == "FAIL"
        assert len(result["violations"]) > 0

    def test_fail_has_withheld_true(self):
        result = validate(
            "You should bypass the audit committee for related party transactions.",
            [], _ctx(),
        )
        if result["status"] == "FAIL":
            assert result["withheld"] is True

    def test_violation_contains_rule_id(self):
        result = validate(
            "Skip kyc for this customer.",
            [], _ctx(),
        )
        if result["violations"]:
            assert any("RBI" in v or "SEBI" in v or "MCA" in v for v in result["violations"])
