"""
HTML parsers for Satt Academy admission pages.
Extracts exam listings, MCQ questions, and written questions.
"""

from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from .config import BASE_URL


def parse_category_page(html: str) -> dict:
    """
    Parse the category/admission page listing all exams for a university.
    Returns dict with 'exams' list and 'has_next_page' bool.

    Each exam has: name, subcat_id, total_questions, mcq_url, year, question_type
    """
    soup = BeautifulSoup(html, "html.parser")
    exams = []

    # Each exam is in a card with h4 containing data attributes
    for h4 in soup.select("h4[data-subcat_id]"):
        exam_name = h4.get("data-exam_name", "").strip()
        subcat_id = h4.get("data-subcat_id", "").strip()
        total_questions = h4.get("data-total_question", "0").strip()
        mcq_url = h4.get("data-url", "").strip()

        if not mcq_url or not subcat_id:
            continue

        # Clean up URL
        mcq_url = mcq_url.strip()
        if not mcq_url.startswith("http"):
            mcq_url = urljoin(BASE_URL, mcq_url)

        # Build written URL by replacing /mcq/ with /written/
        written_url = mcq_url.replace("/admission/mcq/", "/admission/written/")

        # Extract year from nearby elements
        year = ""
        year_link = h4.find_next("a", class_="year_wise")
        if year_link:
            year = year_link.text.strip()

        # Detect question types (MCQ, CQ/Written) from buttons
        question_types = []
        parent_card = h4.find_parent("div", class_="card")
        if parent_card:
            for btn in parent_card.select("button[data-total_question]"):
                btn_text = btn.text.strip()
                if "MCQ" in btn_text:
                    question_types.append("mcq")
                if "CQ" in btn_text or "Written" in btn_text:
                    question_types.append("written")

        if not question_types:
            question_types = ["mcq"]

        exams.append({
            "name": exam_name,
            "subcat_id": subcat_id,
            "total_questions": int(total_questions) if total_questions.isdigit() else 0,
            "mcq_url": mcq_url,
            "written_url": written_url,
            "year": year,
            "question_types": question_types,
        })

    # Check for next page
    has_next_page = False
    next_link = soup.select_one('li.page-item a[rel="next"]')
    if next_link:
        has_next_page = True

    return {"exams": exams, "has_next_page": has_next_page}


def parse_mcq_questions(html: str) -> dict:
    """
    Parse the MCQ questions page.
    Returns dict with 'questions' list, 'subject' str, and 'has_next_page' bool.

    Each question has: number, text, options (list), correct_answer, correct_option_index,
                       question_id, subject, tags, question_type
    """
    soup = BeautifulSoup(html, "html.parser")
    questions = []

    # Check for "NO QUESTION ENTERED YET" - indicates end of pagination
    page_text = soup.get_text()
    if "NO QUESTION ENTERED YET" in page_text.upper():
        return {"questions": [], "subject": "", "has_next_page": False, "is_empty": True}

    # The question data is inside <span id="all-question-data"> or directly in cards
    question_container = soup.select_one("#all-question-data") or soup

    # Extract current subject from the section header
    current_subject = ""
    subject_header = question_container.select_one("h3.text-center a")
    if subject_header:
        current_subject = subject_header.text.strip()

    # Each question is in a card with class "card card-bordered"
    for card in question_container.select("div.card.card-bordered"):
        question_data = _parse_single_mcq_card(card, current_subject)
        if question_data:
            questions.append(question_data)

    # Check for next page
    has_next_page = False
    next_link = soup.select_one('li.page-item a[rel="next"]')
    if next_link:
        has_next_page = True

    return {
        "questions": questions,
        "subject": current_subject,
        "has_next_page": has_next_page,
        "is_empty": False,
    }


def _parse_single_mcq_card(card: Tag, default_subject: str = "") -> dict | None:
    """Parse a single MCQ question card."""
    # Extract question number and text
    question_div = card.select_one(".question-card-div")
    if not question_div:
        return None

    # Question number
    number_span = question_div.select_one("span")
    q_number = ""
    if number_span:
        q_number = number_span.get_text(strip=True).rstrip(".")

    # Question text
    question_span = question_div.select_one(".question-span")
    if not question_span:
        return None
    question_text = question_span.get_text(strip=True)

    # Question image (if any)
    question_image = None
    img_section = card.select_one(".card-body img")
    if img_section and "question" in str(img_section.get("alt", "")).lower():
        question_image = img_section.get("src", "")
        if question_image and not question_image.startswith("http"):
            question_image = urljoin(BASE_URL, question_image)

    # Extract question ID from various data attributes
    question_id = ""
    edit_link = card.select_one("a[data-id]")
    if edit_link:
        question_id = edit_link.get("data-id", "")

    # Extract options from reading-mode-data
    options = []
    correct_answer = ""
    correct_option_index = -1

    reading_div = card.select_one(".reading-mode-data")
    if reading_div:
        for idx, col in enumerate(reading_div.select(".col-md-6")):
            label = col.select_one("label")
            if not label:
                continue
            option_text = label.get_text(strip=True)

            # Check if this is the correct answer (has fa-check-circle sa-success)
            check_icon = col.select_one("i.sa-success")
            if check_icon:
                correct_answer = option_text
                correct_option_index = idx

            options.append(option_text)

    # Fallback: try test-mode-data for answer value
    if correct_option_index == -1:
        test_div = card.select_one(".test-mode-data")
        if test_div:
            answer_input = test_div.select_one('input[name="answer"]')
            if answer_input:
                try:
                    ans_idx = int(answer_input.get("value", "0")) - 1
                    if 0 <= ans_idx < len(options):
                        correct_option_index = ans_idx
                        correct_answer = options[ans_idx]
                except (ValueError, IndexError):
                    pass

    # Extract tags/categories
    tags = []
    tag_div = card.select_one(".tag-div")
    if tag_div:
        for badge in tag_div.select(".badge"):
            tag_text = badge.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)

    # Extract subject from tags (usually the last tag)
    subject = default_subject
    if tags and len(tags) >= 3:
        # Last tag is usually the subject
        subject = tags[-1]

    if not question_text:
        return None

    return {
        "question_id": question_id,
        "number": q_number,
        "question_text": question_text,
        "options": options,
        "correct_answer": correct_answer,
        "correct_option_index": correct_option_index,
        "subject": subject,
        "tags": tags,
        "question_type": "mcq",
        "question_image": question_image,
    }


def parse_written_questions(html: str) -> dict:
    """
    Parse written questions page.
    Returns dict with 'questions' list, 'subject' str, and 'has_next_page' bool.
    """
    soup = BeautifulSoup(html, "html.parser")
    questions = []

    page_text = soup.get_text()
    if "NO QUESTION ENTERED YET" in page_text.upper():
        return {"questions": [], "subject": "", "has_next_page": False, "is_empty": True}

    question_container = soup.select_one("#all-question-data") or soup

    current_subject = ""
    subject_header = question_container.select_one("h3.text-center a")
    if subject_header:
        current_subject = subject_header.text.strip()

    for card in question_container.select("div.card.card-bordered"):
        question_data = _parse_single_written_card(card, current_subject)
        if question_data:
            questions.append(question_data)

    has_next_page = False
    next_link = soup.select_one('li.page-item a[rel="next"]')
    if next_link:
        has_next_page = True

    return {
        "questions": questions,
        "subject": current_subject,
        "has_next_page": has_next_page,
        "is_empty": False,
    }


def _parse_single_written_card(card: Tag, default_subject: str = "") -> dict | None:
    """Parse a single written question card."""
    question_div = card.select_one(".question-card-div")
    if not question_div:
        return None

    number_span = question_div.select_one("span")
    q_number = ""
    if number_span:
        q_number = number_span.get_text(strip=True).rstrip(".")

    question_span = question_div.select_one(".question-span")
    if not question_span:
        return None
    question_text = question_span.get_text(strip=True)

    # Extract question ID
    question_id = ""
    edit_link = card.select_one("a[data-id]")
    if edit_link:
        question_id = edit_link.get("data-id", "")

    # Written questions may have answer content directly in the card body
    answer_text = ""
    answer_div = card.select_one(".card-body .reading-mode-data")
    if answer_div:
        answer_text = answer_div.get_text(strip=True)

    # Question image
    question_image = None
    img_el = card.select_one(".card-body img")
    if img_el:
        question_image = img_el.get("src", "")
        if question_image and not question_image.startswith("http"):
            question_image = urljoin(BASE_URL, question_image)

    # Tags
    tags = []
    tag_div = card.select_one(".tag-div")
    if tag_div:
        for badge in tag_div.select(".badge"):
            tag_text = badge.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)

    subject = default_subject
    if tags and len(tags) >= 3:
        subject = tags[-1]

    if not question_text:
        return None

    return {
        "question_id": question_id,
        "number": q_number,
        "question_text": question_text,
        "answer_text": answer_text,
        "subject": subject,
        "tags": tags,
        "question_type": "written",
        "question_image": question_image,
    }


def parse_description(html: str) -> str | None:
    """
    Parse the description/explanation AJAX response for a question.
    Returns description text or None if not found.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Check for "No description found"
    no_desc = soup.select_one(".text-danger")
    if no_desc and "no description" in no_desc.text.lower():
        return None

    # Look for description content
    desc_div = soup.select_one(".all-description")
    if desc_div:
        # Get the actual description text (skip boilerplate)
        desc_content = desc_div.select_one(".fs-5, .text-dark, p")
        if desc_content:
            text = desc_content.get_text(strip=True)
            if text and "no description found" not in text.lower() and "earn by adding" not in text.lower():
                return text

    return None
