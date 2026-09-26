from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.reports.service import generate_report


router = APIRouter(tags=["v2 Reports"])


MEDIA_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


@router.get("/reports/{analysis_id}/{report_format}")
def download_report(analysis_id: str, report_format: str):
    report_format = report_format.lower()
    try:
        path = generate_report(analysis_id, report_format)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    return FileResponse(
        path=str(path),
        media_type=MEDIA_TYPES[report_format],
        filename=path.name,
    )
