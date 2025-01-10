import React, { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import './FileUpload.css';

const FileUpload = () => {
	const [file, setFile] = useState(null);
	const [analysis, setAnalysis] = useState(null);
	const [gallery, setGallery] = useState([]);
	const [loading, setLoading] = useState(false);
	const fileInputRef = useRef(null);

	const handleFileChange = (e) => {
		setFile(e.target.files[0]);
	};

	const handleUpload = async () => {
		if (!file) {
			alert("Please select a file!");
			return;
		}

		const reader = new FileReader();

		reader.onload = async () => {
			const fileContent = reader.result.split(",")[1];
			const payload = {
				file_name: file.name,
				file_content: fileContent,
			};

			try {
				setLoading(true);

				// Use environment variable for API URL
				const response = await axios.post(
					process.env.REACT_APP_UPLOAD_API_URL,
					payload
				);
				setAnalysis(response.data.analysis);
				fetchGallery();

				if (fileInputRef.current) {
					fileInputRef.current.value = '';
				}
				setFile(null);
			} catch (error) {
				console.error("Upload error:", error);
			} finally {
				setLoading(false);
			}
		};
		reader.readAsDataURL(file);
	};

	const fetchGallery = useCallback(async () => {
		if (loading) return;

		setLoading(true);

		try {
			// Use environment variable for API URL
			const { data } = await axios.get(process.env.REACT_APP_GALLERY_API_URL);
			const body = JSON.parse(data.body);

			if (body?.json_files) {
				const files = body.json_files.map((item) => {
					const labels = item.content.labels || [];
					return {
						file_url: item.content.file_url,
						file_type: item.content.file_type,
						labels,
						last_modified: item.last_modified,
						formattedTimestamp: new Date(item.last_modified).toLocaleString(),
					};
				});

				setGallery(files.sort((a, b) => new Date(b.last_modified) - new Date(a.last_modified)));
			}
		} catch (error) {
			console.error("Error fetching gallery:", error);
		} finally {
			setLoading(false);
		}
	}, [loading]);

	useEffect(() => {
		fetchGallery();
	}, []);

	return (
		<div className="file-upload-container">
			<h1>Upload a File</h1>
			<div className="upload-section">
				<input
					type="file"
					className="file-input"
					onChange={handleFileChange}
					ref={fileInputRef}
				/>
				<button className="upload-button" onClick={handleUpload} disabled={loading}>
					{loading ? "Uploading..." : "Upload"}
				</button>
			</div>
			{analysis && (
				<div className="analysis-results">
					<h2>Analysis Results:</h2>
					<ul>
						{analysis.slice(0, 5).map((label, index) => (
							<li key={index}>
								<strong>{label.Name}</strong> -{" "}
								{label.Confidence.toFixed(2)}%
							</li>
						))}
					</ul>
				</div>
			)}
			<div className="gallery">
				<h2>Gallery</h2>
				<div className="gallery-images">
					{gallery.length === 0 ? (
						<p>No files available.</p>
					) : (
						gallery.map((item, index) => (
							<div className="gallery-item" key={index}>
								{item.file_type === "image" ? (
									<div className="card">
										<img
											src={item.file_url}
											alt={item.file_url}
											className="gallery-image"
										/>
										<div className="card-details">
											<p className="timestamp">
												{item.formattedTimestamp}
											</p>
											<div className="labels">
												{item.labels.slice(0, 5).map((label, i) => (
													<p key={i}>
														<strong>{label.Name}:</strong>{" "}
														{label.Confidence.toFixed(2)}%
													</p>
												))}
											</div>
										</div>
									</div>
								) : (
									<video
										src={item.file_url}
										controls
										className="gallery-video"
									/>
								)}
							</div>
						))
					)}
				</div>
			</div>
		</div>
	);
};

export default FileUpload;
