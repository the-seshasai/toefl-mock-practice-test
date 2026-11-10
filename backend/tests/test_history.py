from tests.flow import create


def test_history_empty(client) -> None:
    assert client.get("/api/history").json() == {"attempts": []}


def test_history_lists_scored_attempts_newest_first(client, llm) -> None:
    from tests.flow import play_section

    a = create(client, section="writing", difficulty="beginner")["id"]
    play_section(client, a, "writing")
    create(client, section="writing", difficulty="beginner")  # never scored: hidden
    items = client.get("/api/history").json()["attempts"]
    assert [i["id"] for i in items] == [a]
    assert items[0]["bands"]["writing"] is not None
