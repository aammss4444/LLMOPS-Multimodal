import React from 'react';

const VideoPlayerSection = ({ videoUrl }) => {
  // Extract YouTube ID from URL to construct embed link
  const getOutputId = (url) => {
    try {
      if (!url) return null;
      const urlObj = new URL(url);
      if (urlObj.hostname.includes('youtube.com')) {
        return urlObj.searchParams.get('v');
      } else if (urlObj.hostname.includes('youtu.be')) {
        return urlObj.pathname.slice(1);
      }
      return null;
    } catch {
      return null;
    }
  };

  const videoId = getOutputId(videoUrl);
  
  // Mock timeline points roughly based on the image's mockup (until backend provides exact timestamp mapping)
  const timelineDots = [
    { type: 'danger', pos: '15%' },
    { type: 'warning', pos: '24%' },
    { type: 'success', pos: '30%' },
    { type: 'success', pos: '90%' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div className="card" style={{ backgroundColor: '#000', borderRadius: '8px', overflow: 'hidden', position: 'relative' }}>
        
        <div style={{ width: '100%', aspectRatio: '16/9', position: 'relative' }}>
          {videoId ? (
            <iframe
              width="100%"
              height="100%"
              src={`https://www.youtube.com/embed/${videoId}?autoplay=0&controls=1`}
              title="YouTube video player"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          ) : (
            <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#1f2937', color: 'white' }}>
              Invalid YouTube URL
            </div>
          )}
        </div>
      </div>
      
      {/* Compliance Timeline Tracker */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
        <span>Compliance Timeline:</span>
        <div style={{ display: 'flex', gap: '6px' }}>
          {timelineDots.map((dot, idx) => (
            <div key={idx} style={{
              width: '12px', height: '12px', borderRadius: '50%',
              backgroundColor: dot.type === 'danger' ? 'var(--danger)' : dot.type === 'warning' ? 'var(--warning)' : 'var(--success)'
            }}></div>
          ))}
        </div>
        <span style={{ marginLeft: '8px', color: 'var(--success)', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'var(--success)' }}></div> Safe
        </span>
      </div>
    </div>
  );
};

export default VideoPlayerSection;
