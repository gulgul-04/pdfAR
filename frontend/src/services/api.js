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
      throw new Error(errorData.detail || `Server Error: ${response.status}`);
    }

    return await response.json();
    
  } catch (error) {
    console.error("API Pipeline Error:", error.message);
    throw error;
  }
};