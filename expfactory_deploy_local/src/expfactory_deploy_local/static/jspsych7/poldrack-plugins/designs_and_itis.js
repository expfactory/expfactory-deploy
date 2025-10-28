// LOADING IN DESIGNS

const loadDesignsAndITIs = async (design_number, design_path, fileNames) => {
  const results = {};

  try {
    // Fetch ITIs
    const itiResponse = await fetch(
      `${design_path}/design_${design_number}/ITIs.txt`
    );
    if (!itiResponse.ok) {
      throw new Error(
        'Network response was not ok for ITIs: ' + itiResponse.statusText
      );
    }
    const itiText = await itiResponse.text();
    results.ITIs = itiText.split('\n');

    // Start the fetch operations for other files concurrently
    const fetchPromises = fileNames.map((fileName) =>
      fetch(`${design_path}/design_${design_number}/${fileName}.txt`)
    );

    // Wait for all fetches to complete
    const responses = await Promise.all(fetchPromises);

    // Check responses for ok status and get text
    await Promise.all(
      responses.map(async (response, index) => {
        if (!response.ok) {
          throw new Error(
            `Network response was not ok for ${fileNames[index]}: ` +
              response.statusText
          );
        }
        const text = await response.text();
        results[fileNames[index]] = text.split('\n');
      })
    );

    return results;
  } catch (error) {
    console.error('There was a problem with the fetch operations:', error);
    return {
      ITIs: [],
      ...Object.fromEntries(fileNames.map((name) => [name, []])),
    };
  }
};
