import { useState, useEffect } from 'react';


import { TestApi } from '../rest/api'
import { AxiosResponse } from 'axios';
const test = new TestApi();



const RestTest = () => {
  const [result, setResult] = useState<any>(null);
  useEffect(() => {
    test.ping().then((r: AxiosResponse) => setResult(r), () => setResult({ data: "API error"}));
  }, []);
    

  return result ? <p>Backend answered: { result.data } </p> : <p>Backend did not answer</p>
}

export default RestTest;