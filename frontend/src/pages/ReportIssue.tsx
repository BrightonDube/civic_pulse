import { useState } from "react";
import type { FormEvent } from "react";
import { createIssue } from "../api/issues";

export default function ReportIssue() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [location, setLocation] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await createIssue({
      title,
      description,
      category: category || null,
      location: location || null,
    });
    setSubmitted(true);
    setTitle("");
    setDescription("");
    setCategory("");
    setLocation("");
  };

  return (
    <section>
      <h2>Report an Issue</h2>
      {submitted && <p>Thanks! Your issue has been submitted.</p>}
      <form onSubmit={handleSubmit}>
        <label>
          Title
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            required
          />
        </label>
        <label>
          Description
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            required
          />
        </label>
        <label>
          Category
          <input
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          />
        </label>
        <label>
          Location
          <input
            value={location}
            onChange={(event) => setLocation(event.target.value)}
          />
        </label>
        <button type="submit">Submit</button>
      </form>
    </section>
  );
}
