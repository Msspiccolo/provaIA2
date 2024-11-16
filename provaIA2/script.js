document.getElementById("uploadForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const fileInput = document.getElementById("fileInput");
    const resultDiv = document.getElementById("result");

    if (!fileInput.files.length) {
        resultDiv.textContent = "Por favor, selecione um arquivo.";
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch("http://127.0.0.1:8000/process-file/", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error("Erro ao processar o arquivo.");
        }

        const data = await response.json();
        resultDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    } catch (error) {
        resultDiv.textContent = `Erro: ${error.message}`;
    }
});
