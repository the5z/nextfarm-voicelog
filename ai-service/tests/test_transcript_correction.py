from app.services.transcript_correction import correct_transcript


def test_correct_ure_variants():
    assert (
        correct_transcript(
            "Bón 15 kg phân U-Ray cho lô B"
        )
        == "Bón 15 kg phân urê cho lô B"
    )

    assert (
        correct_transcript(
            "Bón 15 kg U Re cho lô B"
        )
        == "Bón 15 kg urê cho lô B"
    )

    assert (
        correct_transcript(
            "Bón 15 kg U-Rê cho lô B"
        )
        == "Bón 15 kg urê cho lô B"
    )


def test_correct_npk_letter_variants():
    assert (
        correct_transcript(
            "Bón 20 kg N P K cho lô A"
        )
        == "Bón 20 kg NPK cho lô A"
    )

    assert (
        correct_transcript(
            "Bón 20 kg N.P.K cho lô A"
        )
        == "Bón 20 kg NPK cho lô A"
    )


def test_correct_contextual_npk():
    assert (
        correct_transcript(
            "Bón nờ pê ca cho lô A1"
        )
        == "Bón NPK cho lô A1"
    )

    assert (
        correct_transcript(
            "Dùng phân pê ca cho lô A1"
        )
        == "Dùng phân NPK cho lô A1"
    )


def test_does_not_correct_npk_without_context():
    text = "Mã sản phẩm là pê ca 123"

    assert correct_transcript(text) == text


def test_correct_completed_phrase():
    assert (
        correct_transcript(
            "Công việc đá hoàn thành"
        )
        == "Công việc đã hoàn thành"
    )


def test_correct_harvest_typo():
    assert (
        correct_transcript(
            "Thú hoạch lúa ở lô A1"
        )
        == "thu hoạch lúa ở lô A1"
    )


def test_correct_contextual_weight():
    assert (
        correct_transcript(
            "Thu hoạch lúa được 120k hôm nay"
        )
        == "Thu hoạch lúa được 120 kg hôm nay"
    )


def test_does_not_convert_k_without_agricultural_context():
    text = "Giá sản phẩm là 120k"

    assert correct_transcript(text) == text


def test_does_not_guess_unsafe_values():
    text = (
        "Bỏ 15kg phân U-Ray "
        "cho Lo-B lúc bảy giờ."
    )

    corrected = correct_transcript(text)

    assert "urê" in corrected
    assert "Bỏ" in corrected
    assert "Lo-B" in corrected