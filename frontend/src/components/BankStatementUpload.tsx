import { useState, useRef } from "react";

interface ProgressEvent {
    event: string;
    row?: number;
    total?: number;
    description?: string;
    amount?: number;
    account_code?: string;
    confidence?: number;
    error?: string;
    created?: number;
}

export default function BankStatementUpload({ sessionId }: { sessionId: number }) {
    const [uploading, setUploading] = useState(false);
    const [events, setEvents] = useState<ProgressEvent[]>([]);
    const [done, setDone] = useState(false);
    const abortRef = useRef<AbortController | null>(null);

    const processFile = async (file: File) => {
        if (!file.name.toLowerCase().endsWith(".csv")) return;
        setUploading(true);
        setEvents([]);
        setDone(false);

        const controller = new AbortController();
        abortRef.current = controller;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("http://localhost:8000/api/bank-statements/classify", {
                method: "POST",
                headers: { "X-Session-ID": String(sessionId) },
                body: formData,
                signal: controller.signal,
            });

            if (!res.ok) {
                const err = await res.text();
                alert("Upload failed: " + err);
                setUploading(false);
                return;
            }

            const reader = res.body?.getReader();
            if (!reader) return;

            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done: streamDone, value } = await reader.read();
                if (streamDone) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const evt = JSON.parse(line.slice(6)) as ProgressEvent;
                            setEvents((prev) => [...prev, evt]);
                            if (evt.event === "complete") {
                                setDone(true);
                                setUploading(false);
                            }
                        } catch {

                        }
                    }
                }
            }
        } catch (err: any) {
            if (err.name !== "AbortError") alert ("Error: " + err.message);
        } finally {
            setUploading(false);
            abortRef.current = null;
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file) processFile(file);
    };

    return (
        <div className="p-4 bg-white shadow rounded mt-4">
          <h2 className="text-xl font-bold mb-2">Bank Statement Import</h2>
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className="border-2 border-dashed border-gray-300 rounded p-6 text-center cursor-pointer hover:bg-gray-50"
            onClick={() => document.getElementById("bankfile")?.click()}
          >
            <input
              id="bankfile"
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) processFile(f);
              }}
            />
            {uploading ? "Processing..." : "Drag & drop a CSV bank statement here, or click to select"}
          </div>
    
          {events.length > 0 && (
            <div className="mt-4">
              <h3 className="font-semibold">Classification Progress</h3>
              <div className="max-h-64 overflow-y-auto border rounded p-2 mt-2">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left">
                      <th>Row</th>
                      <th>Description</th>
                      <th>Amount</th>
                      <th>Account</th>
                      <th>Conf.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((evt, i) => {
                      if (evt.event === "error") return (
                        <tr key={i} className="text-red-600">
                          <td>{evt.row}</td>
                          <td colSpan={4}>{evt.error}</td>
                        </tr>
                      );
                      if (evt.event === "complete") return (
                        <tr key={i} className="font-bold text-green-700">
                          <td colSpan={5}>Created {evt.created} transactions</td>
                        </tr>
                      );
                      return (
                        <tr key={i}>
                          <td>{evt.row}/{evt.total}</td>
                          <td>{evt.description}</td>
                          <td>{evt.amount}</td>
                          <td>{evt.account_code}</td>
                          <td>{(evt.confidence ?? 0).toFixed(2)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {done && <p className="mt-4 text-green-600 font-bold">Import finished.</p>}
        </div>
      );
}