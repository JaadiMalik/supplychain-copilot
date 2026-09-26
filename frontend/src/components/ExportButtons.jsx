import { reportUrl } from "../api_v2";


export default function ExportButtons({ analysisId }) {
  if (!analysisId) return null;
  return (
    <div className="v2-export-row">
      {[
        ["pdf", "PDF"],
        ["docx", "DOCX"],
        ["xlsx", "Excel"],
      ].map(([format, label]) => (
        <a
          className="v2-export-button"
          key={format}
          href={reportUrl(analysisId, format)}
          target="_blank"
          rel="noreferrer"
        >
          Export {label}
        </a>
      ))}
    </div>
  );
}
