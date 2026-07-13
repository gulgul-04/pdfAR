const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
const API_KEY = import.meta.env.VITE_API_SECRET_KEY;

export const processPDFs = async (originalFile, editedFile) => {
  const formData = new FormData();
  formData.append("original_pdf", originalFile);
  formData.append("edited_pdf", editedFile);

  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/process-pdfs`, {
      method: "POST",
      headers: {
        "X-API-Key": API_KEY, // The Vault Key
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      let errorMessage = `Server Error: ${response.status}`;
      if (Array.isArray(errorData.detail)) {
        errorMessage = JSON.stringify(errorData.detail[0]); // Grabs the first specific error
      } else if (errorData.detail) {
        errorMessage = errorData.detail;
      }
      
      throw new Error(errorMessage);
    }

    return await response.json();
    
  } catch (error) {
    console.error("API Pipeline Error:", error.message);
    throw error;
  }
};

export const fetchPDFBlob = async (jobId) => {
  const response = await fetch(`${BACKEND_URL}/api/v1/download/${jobId}`, {
    method: "GET",
    headers: {
      "X-API-Key": API_KEY, 
    },
  });

  if (!response.ok) {
    throw new Error("Failed to retrieve file. The secure 15-minute window may have expired.");
  }

  return await response.blob(); 
};

export const injectManualAnnotation = async (jobId, pageNumber, rect, annotData) => {
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
  const API_KEY = import.meta.env.VITE_API_SECRET_KEY;

  const payload = {
    job_id: jobId,
    page_number: pageNumber,
    rect: rect, // { x0, y0, x1, y1 }
    comment_text: annotData.comment_text,
    author: annotData.metadata?.author || "Manual Reviewer",
    annot_type: annotData.type || "Highlight"
  };

  const response = await fetch(`${BACKEND_URL}/api/v1/inject-manual`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to inject annotation.");
  }

  return await response.json();
};