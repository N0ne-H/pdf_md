"""检索排序、长度控制及不同文档上的回归测试。"""

from pathlib import Path

import pytest

from pdf_reader import ReaderService
from pdf_reader.models import Chunk, Document, Page, ParseConfig
from pdf_reader.search import search_chunks


ROOT = Path(__file__).resolve().parents[1]


def _document(contents):
    doc_id = "a" * 64
    chunks = [Chunk(f"c{i:06d}", doc_id, section, i, markdown)
              for i, (section, markdown) in enumerate(contents, 1)]
    return Document(doc_id, "b" * 64, "generic.pdf", "test", ParseConfig(),
                    pages=[Page(i, markdown) for i, (_, markdown) in enumerate(contents, 1)],
                    chunks=chunks)


def test_numbered_targets_and_phrase_beat_repeated_words():
    doc = _document([
        ("Results", "Table 10: attention attention attention training cost"),
        ("Results", "Table 1: sequential operations and path length"),
        ("Results", "Table 2: translation training cost"),
        ("Figures", "Figure 1: encoder decoder structure"),
        ("3.2 Attention", "Scaled dot product attention formula"),
        ("Discussion", "scaled attention dot attention product attention"),
    ])
    assert search_chunks(doc, "Table 1 attention operations").hits[0].chunk_id == "c000002"
    assert search_chunks(doc, "Table 2 training cost").hits[0].chunk_id == "c000003"
    assert search_chunks(doc, "Figure 1 structure").hits[0].chunk_id == "c000004"
    assert search_chunks(doc, "Section 3.2 attention").hits[0].chunk_id == "c000005"
    assert search_chunks(doc, "scaled dot product attention").hits[0].chunk_id == "c000005"


def test_max_chars_is_shared_and_truncation_is_explicit():
    doc = _document([
        (f"Part {i}", "attention answer.\n\n" + "attention details. " * 80)
        for i in range(4)
    ])
    result = search_chunks(doc, "attention", top_k=4, max_chars=200)
    assert len(result.hits) == 4
    assert sum(len(hit.markdown) for hit in result.hits) <= 200
    assert all(hit.markdown and hit.truncated and hit.page_number > 0 for hit in result.hits)
    assert max(len(hit.markdown) for hit in result.hits) < 120
    assert all(hit.markdown.endswith(".") for hit in result.hits)


@pytest.fixture(scope="module")
def real_documents(tmp_path_factory):
    service = ReaderService(tmp_path_factory.mktemp("retrieval"))
    attention = service.ingest(ROOT / "input" / "Attention Is All You Need.pdf").document_id
    trae = service.ingest(ROOT / "input" / "南科大TRAE新手带练手册_吴伟豪.pdf").document_id
    return service, attention, trae


def test_attention_six_question_workflow(real_documents):
    service, attention, _ = real_documents
    queries = [
        "Transformer encoder decoder self-attention recurrence convolution",
        "Scaled Dot-Product Attention sqrt dk softmax gradients",
        "Positional Encoding sine cosine relative positions",
        "self-attention recurrent sequential operations maximum path length Table 1",
        "Table 2 Transformer big BLEU EN-DE EN-FR training cost",
    ]
    results = [service.search(attention, query) for query in queries]
    assert [result.hits[0].chunk_id for result in results] == [
        "c000012", "c000015", "c000023", "c000022", "c000034"
    ]
    assert {hit.chunk_id for hit in results[0].hits} >= {"c000012", "c000019"}
    assert "formula_image" in results[1].hits[0].evidence_warnings
    assert "![](images/" in results[1].hits[0].markdown
    assert "formula_image" in results[2].hits[0].evidence_warnings
    assert "![](images/" in results[2].hits[0].markdown
    assert {hit.chunk_id for hit in results[3].hits} >= {"c000022", "c000026"}
    assert {hit.chunk_id for hit in results[4].hits} >= {"c000034", "c000036"}
    assert "table_structure" in results[4].hits[0].evidence_warnings
    assert results[4].hits[0].truncated  # 精确数字仍须 read 或原页核验。
    assert all(sum(len(hit.markdown) for hit in result.hits) <= 2000 for result in results)

    # Q6 仍先取目录、按章节选择块；检索增强不改变该流程和缓存中的原始页码。
    assert service.outline(attention)
    assert service.read(attention, "c000044").page_number == 10


def test_chinese_expansion_and_other_pdf(real_documents):
    service, attention, trae = real_documents
    chinese = service.search(attention, "缩放点积注意力 公式 梯度")
    english = service.search(attention, "scaled dot product attention formula gradients")
    assert chinese.hits[0].page_number == english.hits[0].page_number == 4
    assert "formula_image" in chinese.hits[0].evidence_warnings
    assert service.search(attention, "表 2 Transformer big 翻译 训练成本").hits[0].chunk_id == "c000034"
    assert [service.search(trae, query).hits[0].page_number for query in (
        "3.2 输入框上的几个按钮",
        "5.4 Skills 沉淀可复用经验",
        "积分消耗过快的四个常见原因",
    )] == [10, 18, 12]
