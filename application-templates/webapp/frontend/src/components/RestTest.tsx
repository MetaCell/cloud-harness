import React, { useState, useEffect } from 'react';


import { TestApi } from '../rest/api'
const test = new TestApi();

const RestTest = () => {
  const [result, setResult] = useState(null);
  useEffect(() => {
    test.ping().then(r => setResult(r), () => setResult({ data: "API error"}));
  }, []);
    

  return result ? <p>Backend answered: { result.data } </p> : <p>Backend did not answer</p>
}

export default RestTest;