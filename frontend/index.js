import axios from "axios";
import { useEffect } from "react";

function App() {
  useEffect(() => {
    axios.get("http://localhost:4000/api/user/test")
      .then(res => {
        console.log(res.data);
      })
      .catch(err => {
        console.error(err);
      });
  }, []);

}

export default App;
