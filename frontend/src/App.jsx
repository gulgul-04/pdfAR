import { useState, useEffect } from 'react';
import { processPDFs, fetchPDFBlob } from './services/api';

function App() {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [appState, setAppState] = useState('landing'); 
  const [isProcessing, setIsProcessing] = useState(false);
  const [originalFile, setOriginalFile] = useState(null);
  const [editedFile, setEditedFile] = useState(null);
  const [status, setStatus] = useState('Idle');
  const [results, setResults] = useState(null);
  const [isReviewMode, setIsReviewMode] = useState(false); 

  // --- NEW: Smart Loading State Variables ---
  const loadingPhrases = [
    "Extracting native dictionary links...",
    "Calculating file geometry...",
    "Running RapidFuzz semantic mapping...",
    "Parsing parent-child thread nodes...",
    "Injecting high-fidelity bounding boxes...",
    "Finalizing document structure..."
  ];
  const [loadingTextIndex, setLoadingTextIndex] = useState(0);
  const [simulatedProgress, setSimulatedProgress] = useState(0);

  // Navbar Morphing Scroll Logic
  useEffect(() => {
    if (appState !== 'landing') return;
    const handleScroll = () => {
      const maxScroll = 350; 
      const progress = Math.min(Math.max(window.scrollY / maxScroll, 0), 1);
      setScrollProgress(progress);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [appState]);

  // Tile & Title Animation Observer
  useEffect(() => {
    if (appState !== 'landing') return;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('opacity-100', 'translate-y-0');
          entry.target.classList.remove('opacity-0', 'translate-y-12');
        }
      });
    }, { threshold: 0.15 });

    const hiddenElements = document.querySelectorAll('.reveal-on-scroll');
    hiddenElements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [appState]);

  // --- NEW: Smart Progress Bar & Text Cycler ---
  useEffect(() => {
    if (!isProcessing) {
      setSimulatedProgress(0);
      setLoadingTextIndex(0);
      return;
    }

    // Trickles the progress bar up to 95%
    const progressInterval = setInterval(() => {
      setSimulatedProgress(old => (old >= 95 ? 95 : old + Math.random() * 8));
    }, 500);

    // Cycles the text but locks onto the final phrase
    const textInterval = setInterval(() => {
      setLoadingTextIndex(prev => Math.min(prev + 1, loadingPhrases.length - 1));
    }, 1500);

    return () => {
      clearInterval(progressInterval);
      clearInterval(textInterval);
    };
  }, [isProcessing, loadingPhrases.length]);

  // Navigation Handlers
  const scrollToSection = (id) => {
    if (appState !== 'landing') {
      setAppState('landing');
      setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }), 50);
    } else {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const scrollToTop = () => {
    if (appState !== 'landing') {
      setAppState('landing');
      setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 50);
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // --- NEW: Execution Logic for Smart Loading ---
  const handleRunPipeline = async () => {
    if (!originalFile || !editedFile) {
      alert("Please select both PDFs first.");
      return;
    }
    setIsProcessing(true);
    setStatus('Processing...');
    setResults(null);
    setIsReviewMode(false); 

    try {
      const data = await processPDFs(originalFile, editedFile);
      
      // Force bar to 100% and delay a moment so the user sees it finish!
      setSimulatedProgress(100);
      await new Promise(resolve => setTimeout(resolve, 600));

      setStatus('Success! All threads restored.');
      setResults(data);
    } catch (error) {
      setStatus(`Failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // --- NEW: Download / Preview Handler ---
  const handleDocumentAction = async (actionType) => {
    try {
      const blob = await fetchPDFBlob(results.download_token);
      const url = window.URL.createObjectURL(blob);
      
      if (actionType === 'download') {
        const a = document.createElement('a');
        a.href = url;
        a.download = `Restored_Annotations.pdf`;
        a.click();
      } else if (actionType === 'preview') {
        // Opens the browser's native PDF viewer in a new tab
        window.open(url, '_blank');
      }
      
      setTimeout(() => window.URL.revokeObjectURL(url), 1000); // Cleanup memory
    } catch (error) {
      alert(error.message);
    }
  };

  // =========================================================================
  // RENDER: TOOL DASHBOARD
  // =========================================================================
  if (appState === 'tool') {
    return (
      <div className="min-h-screen bg-gray-50 text-gray-800 p-10 font-sans">
        <button 
          onClick={scrollToTop}
          className="mb-8 text-sm font-semibold text-gray-500 hover:text-gray-800 transition-colors cursor-pointer flex items-center"
        >
          <span className="mr-2">←</span> Back to Landing Page
        </button>
        
        <div className="max-w-4xl mx-auto bg-white p-10 rounded-2xl shadow-xl border border-gray-100">
          <h1 className="text-3xl font-bold mb-2">PDF Annotation Relocation</h1>
          <p className="text-gray-500 mb-8 font-medium">Secure E2E Enterprise Engine Pipeline</p>
          
          <div className="grid grid-cols-2 gap-8 mb-8">
            <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 hover:border-red-200 transition-colors">
              <h3 className="font-bold mb-4 text-gray-700">1. Original PDF</h3>
              <input type="file" accept="application/pdf" onChange={(e) => setOriginalFile(e.target.files[0])} className="text-sm file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-red-50 file:text-red-700 hover:file:bg-red-100 transition-all cursor-pointer" />
            </div>
            <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 hover:border-red-200 transition-colors">
              <h3 className="font-bold mb-4 text-gray-700">2. Edited PDF</h3>
              <input type="file" accept="application/pdf" onChange={(e) => setEditedFile(e.target.files[0])} className="text-sm file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-red-50 file:text-red-700 hover:file:bg-red-100 transition-all cursor-pointer" />
            </div>
          </div>

          <button 
            onClick={handleRunPipeline}
            disabled={isProcessing}
            className="w-full py-4 bg-[#ED2224] text-white rounded-xl font-bold text-lg hover:bg-red-700 transition-colors shadow-lg cursor-pointer disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isProcessing ? 'Processing Environment...' : 'Process Documents'}
          </button>

          {isProcessing && (
            <div className="mt-8 p-8 border border-gray-100 rounded-2xl bg-gray-50 shadow-inner">
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm font-bold text-[#ED2224] animate-pulse">ENGINE ACTIVE</span>
                <span className="text-xs text-gray-400 font-mono">
                  {simulatedProgress === 100 ? 'Complete' : `Phase ${loadingTextIndex + 1}/6`}
                </span>
              </div>
              <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden mb-6">
                <div 
                  className="h-full bg-[#ED2224] transition-all duration-300 ease-out"
                  style={{ width: `${simulatedProgress}%` }}
                ></div>
              </div>
              <p className="text-gray-600 font-medium text-center h-6 transition-opacity">
                {simulatedProgress === 100 ? "Restoration successful." : loadingPhrases[loadingTextIndex]}
              </p>
            </div>
          )}

          {!isProcessing && status !== 'Idle' && (
            <h3 className={`mt-6 font-semibold text-lg ${status.includes('Failed') ? 'text-red-500' : 'text-emerald-600'}`}>
              Pipeline Status: {status}
            </h3>
          )}

          {results && !isProcessing && !isReviewMode && (
            <div className="mt-8 animate-fade-in">
              <h3 className="text-xl font-bold text-gray-900 mb-6 border-b pb-4">Pipeline Diagnostics</h3>
              
              <div className="grid grid-cols-4 gap-4 mb-8">
                <div className="p-4 bg-gray-50 border border-gray-100 rounded-xl text-center">
                  <div className="text-3xl font-black text-gray-800">{results.total_annotations_found}</div>
                  <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mt-1">Found</div>
                </div>
                <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl text-center">
                  <div className="text-3xl font-black text-emerald-600">{results.successful_matches}</div>
                  <div className="text-xs font-bold text-emerald-700 uppercase tracking-wider mt-1">Auto-Injected</div>
                </div>
                <div className="p-4 bg-amber-50 border border-amber-100 rounded-xl text-center">
                  <div className="text-3xl font-black text-amber-600">{results.needs_review}</div>
                  <div className="text-xs font-bold text-amber-700 uppercase tracking-wider mt-1">Need Review</div>
                </div>
                <div className="p-4 bg-red-50 border border-red-100 rounded-xl text-center">
                  <div className="text-3xl font-black text-red-600">
                    {results.total_annotations_found - results.successful_matches - results.needs_review}
                  </div>
                  <div className="text-xs font-bold text-red-700 uppercase tracking-wider mt-1">Failed</div>
                </div>
              </div>

              {results.needs_review > 0 ? (
                <button 
                  onClick={() => setIsReviewMode(true)}
                  className="w-full py-4 bg-amber-500 text-white rounded-xl font-bold text-lg hover:bg-amber-600 transition-colors shadow-md cursor-pointer"
                >
                  Proceed to Manual Review ({results.needs_review} Items)
                </button>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  <button 
                    onClick={() => handleDocumentAction('preview')}
                    className="w-full py-4 bg-gray-900 text-white rounded-xl font-bold text-lg hover:bg-gray-800 transition-colors shadow-md flex justify-center items-center cursor-pointer"
                  >
                    Preview Document
                  </button>
                  <button 
                    onClick={() => handleDocumentAction('download')}
                    className="w-full py-4 bg-emerald-500 text-white rounded-xl font-bold text-lg hover:bg-emerald-600 transition-colors shadow-md flex justify-center items-center cursor-pointer"
                  >
                    <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                    Download PDF
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // =========================================================================
  // RENDER: CONTACT US PAGE
  // =========================================================================
  if (appState === 'contact') {
    return (
      <div className="min-h-screen bg-gray-50 text-gray-800 p-10 font-sans">
        <button 
          onClick={scrollToTop}
          className="mb-8 text-sm font-semibold text-gray-500 hover:text-gray-800 transition-colors cursor-pointer flex items-center"
        >
          <span className="mr-2">←</span> Back to Landing Page
        </button>

        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-extrabold text-gray-900 mb-4">Get in Touch</h1>
            <p className="text-lg text-gray-500 mb-6">Have questions about our enterprise pipeline? We're here to help.</p>
            
            <div className="inline-flex items-center justify-center space-x-2 bg-red-50 px-6 py-3 rounded-full border border-red-100 text-red-700 font-medium hover:bg-red-100 transition-colors cursor-pointer shadow-sm">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
              </svg>
              <span>
                Prefer email? Reach us at <a href="mailto:john.doe@example.com" className="font-bold hover:underline ml-1">john.doe@example.com</a>
              </span>
            </div>
          </div>

          <div className="bg-white p-10 rounded-3xl shadow-xl border border-gray-100">
            <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); alert('Message sent successfully!'); }}>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">First Name</label>
                  <input type="text" className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-shadow" placeholder="John" />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Last Name</label>
                  <input type="text" className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-shadow" placeholder="Doe" />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Enterprise Email</label>
                <input type="email" className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-shadow" placeholder="john@company.com" />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Message</label>
                <textarea rows="5" className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-shadow resize-none" placeholder="How can we help your team?"></textarea>
              </div>

              <button type="submit" className="w-full py-4 bg-gray-900 text-white rounded-xl font-bold hover:bg-gray-800 transition-colors shadow-md cursor-pointer">
                Send Message
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // =========================================================================
  // RENDER: DYNAMIC LANDING PAGE
  // =========================================================================
  return (
    <div 
      className="min-h-[220vh] bg-gray-50 font-sans selection:bg-red-200"
      style={{
        '--scroll-p': scrollProgress,
        '--shadow-val': scrollProgress > 0 ? '0 10px 25px -5px rgba(0, 0, 0, 0.1)' : '0 20px 25px -5px rgba(0, 0, 0, 0.2)'
      }}
    >
      <div className="morph-nav-container">
        
        <div 
          onClick={() => setAppState('tool')}
          style={{ 
            opacity: 1 - scrollProgress * 3,
            pointerEvents: scrollProgress < 0.2 ? 'auto' : 'none' 
          }} 
          className="absolute inset-0 flex items-center justify-center cursor-pointer text-white font-bold text-xl tracking-wide hover:scale-105 transition-transform"
        >
          START STUDIO
        </div>

        <div 
          style={{ 
            opacity: scrollProgress < 0.5 ? 0 : (scrollProgress - 0.5) * 2,
            pointerEvents: scrollProgress === 1 ? 'auto' : 'none' 
          }}
          className="w-full px-6 flex justify-between items-center text-white"
        >
          <div onClick={scrollToTop} className="font-bold text-xl tracking-wider cursor-pointer pl-2 hover:opacity-80 transition-opacity">PDF<span className="font-light">AR</span></div>
          
          <div className="flex space-x-2 text-sm font-medium items-center">
            <button onClick={scrollToTop} className="px-4 py-2 rounded-lg hover:bg-white/15 hover:text-red-50 transition-all cursor-pointer">Home</button>
            <button onClick={() => scrollToSection('how-it-works')} className="px-4 py-2 rounded-lg hover:bg-white/15 hover:text-red-50 transition-all cursor-pointer">How it Works</button>
            <button onClick={() => scrollToSection('input-requirements')} className="px-4 py-2 rounded-lg hover:bg-white/15 hover:text-red-50 transition-all cursor-pointer">Qualifications</button>
            <button onClick={() => scrollToSection('terms-conditions')} className="px-4 py-2 rounded-lg hover:bg-white/15 hover:text-red-50 transition-all cursor-pointer">Terms</button>
            
            <button onClick={() => setAppState('contact')} className="px-4 py-2 rounded-lg hover:bg-white/15 hover:text-red-50 transition-all cursor-pointer mr-2">Contact Us</button>
            
            <button 
              onClick={() => setAppState('tool')}
              className="px-5 py-2 ml-2 bg-white text-[#ED2224] rounded-full hover:bg-gray-100 hover:shadow-lg hover:-translate-y-0.5 transition-all font-bold shadow-sm cursor-pointer"
            >
              Launch Tool
            </button>
          </div>
        </div>
      </div>

      <div className="h-[95vh] flex flex-col justify-between pt-24 pb-48 text-center px-4 max-w-4xl mx-auto">
        <div className="landing-hero-heading">
          <h1 className="text-6xl font-extrabold text-gray-900 tracking-tight mb-6">
            Semantic Threading for<br/>
            <span className="text-[#ED2224]">Enterprise Documents.</span>
          </h1>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto">
            Port deep annotation histories from draft versions onto clean, modern engineering templates instantly.
          </p>
        </div>
        
        <div className="landing-hero-text animate-bounce text-gray-400 font-semibold text-sm tracking-widest mt-auto">
          ↓ SCROLL DOWN TO EXPLORE REQUIREMENTS
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-8 pb-32 space-y-16">
        
        <div id="how-it-works" className="bg-white rounded-3xl p-12 shadow-xl border border-gray-100 scroll-mt-24">
          <h2 className="reveal-on-scroll opacity-0 translate-y-12 transition-all duration-700 ease-out text-3xl font-bold text-gray-900 mb-6">
            Intelligent Annotation Relocation
          </h2>
          <div className="reveal-on-scroll opacity-0 translate-y-12 transition-all duration-700 delay-150 ease-out">
            <p className="text-lg text-gray-600 leading-relaxed mb-8">
              When structural layouts undergo breaking transformations, native comments, text strings, and context histories get broken. Our system bridges that gap by mapping local paragraph blocks, identifying relative structural coordinates, and parsing low-level threads.
            </p>
            <div className="grid grid-cols-3 gap-6">
              <div className="p-6 bg-gray-50 rounded-2xl hover:shadow-md transition-shadow">
                <div className="text-[#ED2224] text-2xl mb-4 font-black">01</div>
                <h4 className="font-bold text-gray-900 mb-2">Extract</h4>
                <p className="text-sm text-gray-500">Maps native dictionary links, thread nodes, and author metadata flags cleanly.</p>
              </div>
              <div className="p-6 bg-gray-50 rounded-2xl hover:shadow-md transition-shadow">
                <div className="text-[#ED2224] text-2xl mb-4 font-black">02</div>
                <h4 className="font-bold text-gray-900 mb-2">Match</h4>
                <p className="text-sm text-gray-500">Runs sliding-window calculations via Proximity Heuristics across modified pages.</p>
              </div>
              <div className="p-6 bg-gray-50 rounded-2xl hover:shadow-md transition-shadow">
                <div className="text-[#ED2224] text-2xl mb-4 font-black">03</div>
                <h4 className="font-bold text-gray-900 mb-2">Inject</h4>
                <p className="text-sm text-gray-500">Reconstructs exact high-fidelity bounding boxes and threads into the document.</p>
              </div>
            </div>
          </div>
        </div>

        <div id="input-requirements" className="grid grid-cols-2 gap-12 scroll-mt-24">
          <div className="reveal-on-scroll opacity-0 translate-y-12 transition-all duration-700 ease-out">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Input Matrix Qualifications</h2>
            <ul className="space-y-4">
              <li className="flex items-start">
                <span className="text-[#ED2224] mr-3 mt-1">●</span>
                <span className="text-gray-600"><strong>Source Drafts:</strong> Must use native interactive comment properties (Highlight, Caret, FreeText, Redact).</span>
              </li>
              <li className="flex items-start">
                <span className="text-[#ED2224] mr-3 mt-1">●</span>
                <span className="text-gray-600"><strong>Target Files:</strong> Clean updated templates completely stripped of older annotations.</span>
              </li>
              <li className="flex items-start">
                <span className="text-[#ED2224] mr-3 mt-1">●</span>
                <span className="text-gray-600"><strong>Text Layers:</strong> Fully searchable character maps are required. Scanned graphical images are rejected.</span>
              </li>
            </ul>
          </div>

          <div className="reveal-on-scroll opacity-0 translate-y-12 transition-all duration-700 delay-200 ease-out bg-gray-900 rounded-3xl p-10 text-white shadow-2xl relative overflow-hidden group hover:scale-[1.02] transition-transform cursor-default">
             <h2 className="text-2xl font-bold mb-6 text-red-500">Secure Vault Framework</h2>
             <div className="space-y-4 relative z-10">
                <div>
                  <div className="text-gray-400 text-xs uppercase font-bold tracking-wider">Max Upload Cap</div>
                  <div className="text-2xl font-light group-hover:text-red-200 transition-colors">50 Megabytes</div>
                </div>
                <div>
                  <div className="text-gray-400 text-xs uppercase font-bold tracking-wider">Max Compilation Ceiling</div>
                  <div className="text-2xl font-light group-hover:text-red-200 transition-colors">500 Context Pages</div>
                </div>
                <div>
                  <div className="text-gray-400 text-xs uppercase font-bold tracking-wider">Complexity Filter Threshold</div>
                  <div className="text-2xl font-light group-hover:text-red-200 transition-colors">1,000 Total Nodes</div>
                </div>
             </div>
          </div>
        </div>

        <div id="terms-conditions" className="reveal-on-scroll opacity-0 translate-y-12 transition-all duration-700 ease-out bg-white rounded-3xl p-12 shadow-md border border-gray-100 scroll-mt-24">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Terms & Local Sandbox Framework</h2>
          <p className="text-sm text-gray-500 leading-relaxed delay-100 transition-opacity">
            This platform executes all computational matching via a sandboxed pipeline architecture. Job directories are securely decoupled via ephemeral virtual workspaces, and source assets are permanently scrubbed from active environments within fifteen minutes of processing termination. All processes strictly conform to localized data privacy governance architectures.
          </p>
        </div>

      </div>
    </div>
  );
}

export default App;