export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="auth-bg">
      <div className="auth-orb auth-orb-1" />
      <div className="auth-orb auth-orb-2" />
      <div className="auth-center">{children}</div>
      <style>{`
        .auth-bg {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          overflow: hidden;
          padding: 2rem 1rem;
        }
        .auth-center {
          position: relative;
          z-index: 1;
          width: 100%;
          display: flex;
          justify-content: center;
        }
        .auth-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          pointer-events: none;
        }
        .auth-orb-1 {
          width: 600px;
          height: 600px;
          background: radial-gradient(circle, rgba(124, 106, 247, 0.18) 0%, transparent 70%);
          top: -200px;
          left: -150px;
        }
        .auth-orb-2 {
          width: 500px;
          height: 500px;
          background: radial-gradient(circle, rgba(78, 205, 196, 0.1) 0%, transparent 70%);
          bottom: -150px;
          right: -100px;
        }
      `}</style>
    </div>
  );
}
