// frontend/src/ReviewMode.jsx
import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { injectManualAnnotation } from './services/api';

// Required for Vite to load the PDF.js web worker correctly
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

export default function ReviewMode({ jobId, initialQueue, onComplete }) {
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
  const API_KEY = import.meta.env.VITE_API_SECRET_KEY;
  
  // Create a secure URL to fetch the live preview from the backend
  const previewUrl = `${BACKEND_URL}/api/v1/preview/${jobId}`;

  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [reviewQueue, setReviewQueue] = useState(initialQueue);
  const [selectedAnnot, setSelectedAnnot] = useState(null);
  const [isInjecting, setIsInjecting] = useState(false);
  const [pdfKey, setPdfKey] = useState(0); // Used to force-reload the PDF after injection

  // Mouse Tracking State for the Highlight Box
  const [isDragging, setIsDragging] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [currentBox, setCurrentBox] = useState(null);

  // === MOUSE DRAG LOGIC ===
  const handleMouseDown = (e) => {
    if (!selectedAnnot || isInjecting) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setStartPos({ x, y });
    setIsDragging(true);
    setCurrentBox({ x, y, w: 0, h: 0 });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setCurrentBox({
      x: Math.min(x, startPos.x),
      y: Math.min(y, startPos.y),
      w: Math.abs(x - startPos.x),
      h: Math.abs(y - startPos.y)
    });
  };

  const handleMouseUp = async () => {
    if (!isDragging) return;
    setIsDragging(false);

    // If the box is big enough, trigger the API
    if (currentBox && currentBox.w > 5 && currentBox.h > 5) {
      await handleInjectAnnotation();
    } else {
      setCurrentBox(null);
    }
  };

  // === API INJECTION LOGIC ===
  const handleInjectAnnotation = async () => {
    setIsInjecting(true);
    try {
      // Map HTML CSS pixels (at scale 1.0) directly to PDF Points
      const pdfRect = {
        x0: currentBox.x,
        y0: currentBox.y,
        x1: currentBox.x + currentBox.w,
        y1: currentBox.y + currentBox.h
      };

      // Note: pageNumber in react-pdf is 1-indexed, PyMuPDF is 0-indexed
      await injectManualAnnotation(jobId, pageNumber - 1, pdfRect, selectedAnnot);

      // Remove the successfully injected item from the queue
      const newQueue = reviewQueue.filter(item => item.original_id !== selectedAnnot.original_id);
      setReviewQueue(newQueue);
      setSelectedAnnot(null);
      setCurrentBox(null);
      
      // Force the PDF viewer to refresh so the user sees the new highlight!
      setPdfKey(prev => prev + 1); 

    } catch (error) {
      alert(`Injection Failed: ${error.message}`);
      setCurrentBox(null);
    } finally {
      setIsInjecting(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 font-sans overflow-hidden">
      
      {/* LEFT SIDE: PDF Viewer */}
      <div className="flex-1 flex flex-col relative bg-gray-300 overflow-y-auto items-center py-8">
        
        {/* Floating Page Controls */}
        <div className="fixed top-6 bg-gray-900 text-white px-6 py-3 rounded-full shadow-2xl z-50 flex items-center space-x-6">
          <button 
            disabled={pageNumber <= 1} 
            onClick={() => setPageNumber(p => p - 1)}
            className="hover:text-red-400 disabled:opacity-50 transition-colors font-bold"
          >
            &larr; Prev
          </button>
          <span className="font-mono text-sm">Page {pageNumber} of {numPages || '--'}</span>
          <button 
            disabled={pageNumber >= numPages} 
            onClick={() => setPageNumber(p => p + 1)}
            className="hover:text-red-400 disabled:opacity-50 transition-colors font-bold"
          >
            Next &rarr;
          </button>
        </div>

        {/* The PDF Document Render */}
        <div className="mt-12 bg-white shadow-2xl relative select-none">
          <Document
            key={pdfKey}
            file={{ url: previewUrl, httpHeaders: { "X-API-Key": API_KEY } }}
            onLoadSuccess={({ numPages }) => setNumPages(numPages)}
            loading={<div className="p-20 text-gray-500 animate-pulse">Rendering Secure Document...</div>}
          >
            {/* The Mouse Tracking Layer */}
            <div 
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={() => setIsDragging(false)}
              className={`relative ${selectedAnnot ? 'cursor-crosshair' : 'cursor-default'}`}
            >
              <Page 
                pageNumber={pageNumber} 
                scale={1.0} 
                renderTextLayer={true}
                renderAnnotationLayer={true}
              />
              
              {/* The Blue Highlight Box that draws with your mouse */}
              {currentBox && (
                <div 
                  className="absolute border-2 border-blue-500 bg-blue-300 opacity-40 pointer-events-none"
                  style={{
                    left: currentBox.x,
                    top: currentBox.y,
                    width: currentBox.w,
                    height: currentBox.h
                  }}
                />
              )}
            </div>
          </Document>
          
          {/* Loading Overlay when API is injecting */}
          {isInjecting && (
            <div className="absolute inset-0 bg-white/70 flex items-center justify-center z-50">
              <div className="px-6 py-3 bg-red-600 text-white font-bold rounded-full shadow-lg animate-bounce">
                Injecting Annotation...
              </div>
            </div>
          )}
        </div>
      </div>

      {/* RIGHT SIDE: Orphaned Thread Queue */}
      <div className="w-96 bg-white shadow-[-10px_0_20px_rgba(0,0,0,0.05)] border-l border-gray-200 flex flex-col z-10">
        <div className="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Review Queue</h2>
            <p className="text-sm text-amber-600 font-semibold">{reviewQueue.length} Items Remaining</p>
          </div>
          <button 
             onClick={onComplete}
             className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-bold hover:bg-gray-800 transition-colors"
          >
             Done
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {reviewQueue.length === 0 ? (
            <div className="text-center text-emerald-500 font-bold p-8 border-2 border-dashed border-emerald-200 rounded-xl bg-emerald-50">
              All threads restored!
            </div>
          ) : (
            reviewQueue.map((annot) => (
              <div 
                key={annot.original_id}
                onClick={() => setSelectedAnnot(annot)}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedAnnot?.original_id === annot.original_id 
                    ? 'border-red-500 bg-red-50 shadow-md' 
                    : 'border-gray-100 hover:border-gray-300 bg-white'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center">
                    {annot.metadata?.author || 'Unknown'}
                  </span>
                  {annot.parent_id && (
                     <span className="text-[10px] px-2 py-1 bg-gray-200 text-gray-600 rounded-full font-bold">Reply</span>
                  )}
                </div>
                <p className="text-sm text-gray-800 font-medium mb-3">"{annot.comment_text}"</p>
                <div className="text-xs bg-gray-100 p-2 rounded text-gray-500 font-mono italic">
                  Lost Anchor: "{annot.anchor_text ? annot.anchor_text.substring(0, 40) + '...' : 'No anchor'}"
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}