"""
ClassMind - Classroom polling helpers.

Wraps the Classroom API calls needed to detect new slide-based material
across your tracked courses. Checks two places, since teachers might
post slides either way:

- courseWorkMaterials: standalone "material" posts (most likely, since
  LGU policy is slides-only, no graded work attached)
- courseWork: assignments that happen to carry a slide-deck attachment

Both return Drive file references, which drive_extract.py then turns
into actual text.
"""

from googleapiclient.discovery import build


def get_classroom_service(creds):
    return build("classroom", "v1", credentials=creds)


def list_courses(service) -> list[dict]:
    courses = []
    page_token = None
    while True:
        resp = (
            service.courses()
            .list(pageToken=page_token, courseStates=["ACTIVE"])
            .execute()
        )
        courses.extend(resp.get("courses", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return courses


def _extract_drive_files(materials: list[dict] | None) -> list[dict]:
    """Pulls DriveFile dicts out of a list of Classroom Material objects."""
    drive_files = []
    for m in materials or []:
        shared = m.get("driveFile")
        if shared and shared.get("driveFile"):
            drive_files.append(shared["driveFile"])
    return drive_files


def list_new_course_materials(service, course_id: str) -> list[dict]:
    """
    Returns every Drive-attached post in this course as a flat list of dicts:
    {post_id, course_id, post_title, drive_file_id, drive_file_title, kind, update_time}

    Does not filter by "already seen" — poller.py handles dedup, since
    that state needs to persist across runs.
    """
    items = []

    # Standalone material posts.
    page_token = None
    while True:
        resp = (
            service.courses()
            .courseWorkMaterials()
            .list(courseId=course_id, pageToken=page_token, pageSize=50)
            .execute()
        )
        for cwm in resp.get("courseWorkMaterial", []):
            for df in _extract_drive_files(cwm.get("materials")):
                items.append(
                    {
                        "post_id": cwm["id"],
                        "course_id": course_id,
                        "post_title": cwm.get("title", "Untitled"),
                        "drive_file_id": df["id"],
                        "drive_file_title": df.get("title", "Untitled"),
                        "kind": "courseWorkMaterial",
                        "update_time": cwm.get("updateTime"),
                    }
                )
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    # Assignments that happen to carry a slide-deck attachment.
    page_token = None
    while True:
        resp = (
            service.courses()
            .courseWork()
            .list(courseId=course_id, pageToken=page_token, pageSize=50)
            .execute()
        )
        for cw in resp.get("courseWork", []):
            for df in _extract_drive_files(cw.get("materials")):
                items.append(
                    {
                        "post_id": cw["id"],
                        "course_id": course_id,
                        "post_title": cw.get("title", "Untitled"),
                        "drive_file_id": df["id"],
                        "drive_file_title": df.get("title", "Untitled"),
                        "kind": "courseWork",
                        "update_time": cw.get("updateTime"),
                    }
                )
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return items
