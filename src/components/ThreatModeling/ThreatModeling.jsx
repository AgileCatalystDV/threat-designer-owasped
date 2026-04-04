import { useEffect, useState } from "react";
import SpaceBetween from "@cloudscape-design/components/space-between";
import { SubmissionComponent } from "./SubmissionForm";
import { Alert, Modal } from "@cloudscape-design/components";
import { uploadFile } from "./docs";
import { useNavigate } from "react-router-dom";
import { startThreatModeling, generateUrl } from "../../services/ThreatDesigner/stats";
import GenAiButton from "../../components/ThreatModeling/GenAiButton";
import "./ThreatModeling.css";

export default function ThreatModeling() {
  const [iteration, setIteration] = useState({ label: "Auto", value: 0 });
  const [reasoning, setReasoning] = useState("0");
  const [base64Content, setBase64Content] = useState(null);
  const [id, setId] = useState(null);
  const [visible, setVisible] = useState(false);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [startError, setStartError] = useState(null);

  const handleBase64Change = (base64) => {
    setBase64Content(base64);
  };

  const handleStartThreatModeling = async (title, description, assumptions, applicationType) => {
    setLoading(true);
    setStartError(null);
    try {
      const results = await generateUrl(base64Content?.type);
      await uploadFile(base64Content?.value, results?.data?.presigned, base64Content?.type);
      const response = await startThreatModeling(
        results?.data?.name,
        iteration?.value,
        reasoning,
        title,
        description,
        assumptions,
        false, // replay
        null, // id
        null, // instructions
        base64Content?.type, // imageType
        applicationType
      );
      setLoading(false);
      setId(response.data.id);
    } catch (error) {
      console.error("Error starting threat modeling:", error);
      const apiMsg = error?.response?.data?.message;
      const fallback = error?.message ?? String(error);
      setStartError(typeof apiMsg === "string" ? apiMsg : fallback);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      navigate(`/${id}`);
    }
  }, [id, navigate]);

  return (
    <SpaceBetween size="s">
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <div style={{ marginTop: "200px" }}>
          <GenAiButton
            onClick={() => {
              setStartError(null);
              setVisible(true);
            }}
          >
            Submit Threat Model
          </GenAiButton>
        </div>
      </div>
      <Modal
        onDismiss={() => {
          setVisible(false);
          setStartError(null);
        }}
        visible={visible}
        size="large"
        header={"Threat model"}
      >
        <SpaceBetween size="m">
          {startError ? (
            <Alert
              type="error"
              statusIconAriaLabel="Error"
              header="Could not start threat modeling"
              dismissible
              onDismiss={() => setStartError(null)}
            >
              {startError}
            </Alert>
          ) : null}
          <SubmissionComponent
            onBase64Change={handleBase64Change}
            base64Content={base64Content}
            iteration={iteration}
            setIteration={setIteration}
            setVisible={setVisible}
            handleStart={handleStartThreatModeling}
            loading={loading}
            reasoning={reasoning}
            setReasoning={setReasoning}
          />
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  );
}
