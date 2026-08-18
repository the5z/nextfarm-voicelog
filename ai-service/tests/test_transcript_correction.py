from app.services.transcript_correction import correct_transcript


def test_correct_ure_variants():
    assert (
        correct_transcript(
            "Bón 15 kg phần U-Ray cho lô B"
        )
        == "Bón 15 kg phần urê cho lô B"
    )

    assert (
        correct_transcript(
            "Bón 15 kg U Re cho lô B"
        )
        == "Bón 15 kg urê cho lô B"
    )


def test_correct_npk_variants():
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


def test_does_not_guess_unsafe_values():
    text = (
        "Bỏ 15kg phần U-Ray "
        "cho Lo-B lúc bảy giờ."
    )

    corrected = correct_transcript(
        text
    )

    assert "urê" in corrected

    # Các phần chưa đủ chắc chắn thì giữ nguyên.
    assert "Bỏ" in corrected
    assert "phần" in corrected
    assert "Lo-B" in corrected