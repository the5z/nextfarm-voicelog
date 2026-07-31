import Header from "../components/Header";
import RecordButton from "../components/RecordButton";
import TranscriptBox from "../components/TranscriptBox";
import AIForm from "../components/AIForm";
import ActionButtons from "../components/ActionButtons";

function VoiceLog() {
  return (
    <div className="container">
      <Header />

      <RecordButton />

      <TranscriptBox />

      <AIForm />

      <ActionButtons />
    </div>
  );
}

export default VoiceLog;