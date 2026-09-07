from app.handlers import admin
from app.services import post_footer


def test_get_post_footer_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        post_footer, "POST_FOOTER_FILE", tmp_path / "post_footer.txt"
    )
    assert post_footer.get_post_footer() == ""


def test_get_post_footer_reads_and_strips_whitespace(tmp_path, monkeypatch):
    footer_file = tmp_path / "post_footer.txt"
    footer_file.write_text(
        "  \n📺 Другие каналы: <a href=\"https://t.me/x\">тут</a>\n  ",
        encoding="utf-8",
    )
    monkeypatch.setattr(post_footer, "POST_FOOTER_FILE", footer_file)

    assert (
        post_footer.get_post_footer()
        == '📺 Другие каналы: <a href="https://t.me/x">тут</a>'
    )


def test_format_post_caption_without_footer(monkeypatch):
    monkeypatch.setattr(admin, "get_post_footer", lambda: "")

    caption = admin.format_post_caption("Title", "https://example.com/v")

    assert caption == (
        '<b>Title</b>\n\n🔗 <a href="https://example.com/v">Смотреть видео</a>'
    )


def test_format_post_caption_appends_footer(monkeypatch):
    monkeypatch.setattr(
        admin, "get_post_footer", lambda: "<tg-spoiler>ссылка</tg-spoiler>"
    )

    caption = admin.format_post_caption("Title", "https://example.com/v")

    assert caption == (
        '<b>Title</b>\n\n🔗 <a href="https://example.com/v">Смотреть видео</a>'
        "\n\n<tg-spoiler>ссылка</tg-spoiler>"
    )
