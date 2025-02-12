import { useState, useEffect } from "react";
import Chat from "./Chat";
import UploadModal from "./components/UploadModal";
import "./index.css";
import "./App.css";

const API_BASE_URL = "http://localhost:8080";

function App() {
  const [view, setView] = useState<"chat" | "collections">("chat");
  const [collections, setCollections] = useState<string[]>([]);
  const [selectedCollection, setSelectedCollection] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleCollectionChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCollection(event.target.value);
  };

  useEffect(() => {
    const fetchCollections = async () => {
      try {
        console.log("Fetching collections...");
        const response = await fetch(`${API_BASE_URL}/collections`);

        if (!response.ok) throw new Error("Failed to fetch collections");

        const data = await response.json();

        if (Array.isArray(data) && data.length > 0) {
          setCollections(data);
          setSelectedCollection(data[0]); // Select first collection if available
        } else {
          setCollections([]); // Keep it empty
          setSelectedCollection(""); // No default selection
        }

      } catch (error) {
        console.error("Error fetching collections:", error);
        setCollections([]); // Ensure it's empty on error
        setSelectedCollection(""); // No default selection
      }
    };

    fetchCollections();
  }, []);

  const handleUpload = async (collectionName: string, files: FileList | null) => {
    console.log("handle upload called with: ", collectionName)
    if (!collectionName.trim() || !files) {
      console.log("Upload conditions not met, exiting...");
      return;
    }

    const formData = new FormData();
    formData.append("collection_name", collectionName);
    Array.from(files).forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await fetch(`${API_BASE_URL}/upload_pdfs`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Upload failed");
      console.log("Upload successful!");
      setCollections([...collections, collectionName]);
    } catch (error) {
      console.error("Upload error:", error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex">
      {/* Left Side: Main Content */}
      <div className="flex flex-col flex-grow">
        <header className="bg-gray-800 text-white text-center p-4">
          Code Challenge: Build a RAG Chat App
        </header>

        <main className="flex-grow container mx-auto p-3 flex flex-col">
          {view === "chat" && <Chat selectedCollection={selectedCollection} />}
        </main>
      </div>

      {/* Right Side Navbar */}
      <div className="w-64 bg-gray-800 p-4 text-white flex flex-col">
        <h2 className="text-lg font-bold mb-4">Menu</h2>
        <button
          className={`p-2 mb-2 rounded ${view === "chat" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}
          onClick={() => setView("chat")}
        >
          Chat
        </button>

        {/* Dropdown for Collection Selection */}
        <label className="mt-4 text-sm">Select Collection:</label>
        <select
          className="p-2 bg-gray-700 text-white rounded mt-2"
          value={selectedCollection}
          onChange={handleCollectionChange}
          disabled={collections.length === 0} // Disable dropdown if no collections exist
        >
          {collections.map((collection) => (
            <option key={collection} value={collection}>
              {collection}
            </option>
          ))}
        </select>

        <button
          className={`p-2 rounded ${view === "collections" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}
          onClick={() => setIsModalOpen(true)}
        >
          Manage Collections
        </button>

        {/* Message when no collections exist */}
        {collections.length === 0 && (
          <p className="text-red-500 text-sm mt-2">
            No collections available. Please upload a collection first.
          </p>
        )}
      </div>

      <UploadModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onUpload={handleUpload} />
    </div>
  );
}

export default App;
