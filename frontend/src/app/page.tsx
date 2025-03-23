// frontend/app/page.tsx
import VoiceChatUI from '../../components/VoiceChatUI';

export default function Home() {
  return (
    <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#f0f0f0'
    }}>
      <VoiceChatUI />
    </div>
  );
}