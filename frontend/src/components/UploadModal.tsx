import React, { useState } from "react";
import "../index.css";

interface UploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUpload: (collectionName: string, files: FileList | null) => void;
}

const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onUpload }) => {
    const [collectionName, setCollectionName] = useState("");
    const [files, setFiles] = useState<FileList | null>(null);

    if (!isOpen) return null;

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setFiles(event.target.files);
    };

    const handleUpload = () => {
        if (!collectionName.trim() || !files) return;
        onUpload(collectionName, files);
        setCollectionName("");
        setFiles(null);
        onClose();
    };

    return (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-96 text-white">
                <h2 className="text-lg font-bold mb-4">Add New Collection</h2>

                <input
                    type="text"
                    placeholder="Collection Name"
                    value={collectionName}
                    onChange={(e) => setCollectionName(e.target.value)}
                    className="w-full p-2 border rounded bg-gray-900 text-white"
                />

                <input
                    type="file"
                    multiple
                    accept="application/pdf, text/plain"
                    onChange={handleFileChange}
                    className="w-full p-2 mt-3 border rounded bg-gray-900 text-white"
                />

                <div className="flex justify-between mt-4">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleUpload}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
                    >
                        Upload
                    </button>
                </div>
            </div>
        </div>
    );
};

export default UploadModal;
