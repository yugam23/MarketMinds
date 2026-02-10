/**
 * Footer Component
 * Data attributions and links.
 */
import './Footer.css';

export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <p className="footer-text">
          © 2026 MarketMinds. AI-powered price predictions with sentiment analysis.
        </p>
        <div className="footer-links">
          <span className="footer-attribution">
            Data: <a href="https://finance.yahoo.com" target="_blank" rel="noopener noreferrer">Yahoo Finance</a> | 
            Sentiment: <a href="https://huggingface.co/ProsusAI/finbert" target="_blank" rel="noopener noreferrer">FinBERT</a>
          </span>
        </div>
      </div>
    </footer>
  );
}
