from app.agents.company_list.agent import (
    _MIN_SEMANTIC_SCORE,
    _build_broaden_suggestions,
    _build_pinecone_filter,
    _format_company,
    _score_to_pct,
)


class TestBuildPineconeFilter:
    def test_no_params_returns_none(self) -> None:
        assert _build_pinecone_filter() is None

    def test_country_only(self) -> None:
        assert _build_pinecone_filter(country="FR") == {"country": "FR"}

    def test_min_employees_only(self) -> None:
        f = _build_pinecone_filter(min_employees=50)
        assert f == {"employees_count": {"$gte": 50}}

    def test_max_employees_only(self) -> None:
        f = _build_pinecone_filter(max_employees=500)
        assert f == {"employees_count": {"$lte": 500}}

    def test_employee_range(self) -> None:
        f = _build_pinecone_filter(min_employees=50, max_employees=500)
        assert f == {"employees_count": {"$gte": 50, "$lte": 500}}

    def test_industries(self) -> None:
        f = _build_pinecone_filter(industries=["Software Development", "IT Services and IT Consulting"])
        assert f == {"industry": {"$in": ["Software Development", "IT Services and IT Consulting"]}}

    def test_hiring_true(self) -> None:
        assert _build_pinecone_filter(hiring=True) == {"hiring": True}

    def test_hiring_false(self) -> None:
        assert _build_pinecone_filter(hiring=False) == {"hiring": False}

    def test_headcount_increasing(self) -> None:
        f = _build_pinecone_filter(headcount_increasing=True)
        assert f == {"headcount_increasing": True}

    def test_all_filters_combined(self) -> None:
        f = _build_pinecone_filter(
            country="FR",
            industries=["Software Development"],
            min_employees=50,
            max_employees=200,
            hiring=True,
        )
        assert f is not None
        assert f["country"] == "FR"
        assert f["industry"] == {"$in": ["Software Development"]}
        assert f["employees_count"] == {"$gte": 50, "$lte": 200}
        assert f["hiring"] is True


class TestScoreToPct:
    def test_min_score_maps_to_zero(self) -> None:
        assert _score_to_pct(_MIN_SEMANTIC_SCORE) == 0

    def test_max_score_maps_to_hundred(self) -> None:
        assert _score_to_pct(1.0) == 100

    def test_below_min_clamped_to_zero(self) -> None:
        assert _score_to_pct(0.0) == 0

    def test_above_max_clamped_to_hundred(self) -> None:
        assert _score_to_pct(1.5) == 100

    def test_midpoint(self) -> None:
        mid = (_MIN_SEMANTIC_SCORE + 1.0) / 2
        assert _score_to_pct(mid) == 50


class TestFormatCompany:
    def test_full_company(self) -> None:
        c = {
            "company_key": "linkedin_id:123",
            "name": "Acme",
            "domain": "acme.com",
            "linkedin_url": "https://linkedin.com/company/acme",
            "industry": "Software Development",
            "employees_count": 150,
            "country": "FR",
            "icp_score": 85,
        }
        result = _format_company(c)
        assert result["name"] == "Acme"
        assert result["domain"] == "acme.com"
        assert result["size"] == "150"
        assert result["icp_score"] == 85
        assert result["country"] == "FR"
        assert result["linkedin_url"] == "https://linkedin.com/company/acme"

    def test_missing_employees_gives_empty_size(self) -> None:
        c = {"employees_count": None, "icp_score": 0}
        assert _format_company(c)["size"] == ""

    def test_none_name_gives_empty_string(self) -> None:
        c = {"name": None, "icp_score": 0}
        assert _format_company(c)["name"] == ""

    def test_none_domain_gives_empty_string(self) -> None:
        c = {"domain": None, "icp_score": 0}
        assert _format_company(c)["domain"] == ""


class TestBuildBroadenSuggestions:
    def test_no_filters_gives_empty(self) -> None:
        assert _build_broaden_suggestions({}) == []

    def test_size_filter_triggers_suggestion(self) -> None:
        result = _build_broaden_suggestions({"min_employees": 50})
        assert len(result) == 1
        assert "label" in result[0]
        assert "hint" in result[0]

    def test_country_filter_triggers_suggestion(self) -> None:
        result = _build_broaden_suggestions({"country": "FR"})
        assert len(result) == 1

    def test_industry_filter_triggers_suggestion(self) -> None:
        result = _build_broaden_suggestions({"industries": ["Software Development"]})
        assert len(result) == 1

    def test_all_filters_capped_at_three(self) -> None:
        result = _build_broaden_suggestions({
            "country": "FR",
            "min_employees": 50,
            "industries": ["Software Development"],
        })
        assert len(result) == 3

    def test_suggestions_have_label_and_hint(self) -> None:
        result = _build_broaden_suggestions({"country": "FR"})
        assert result[0]["label"]
        assert result[0]["hint"]
