import React, { useEffect, useState } from 'react'
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null);

    const getStats = () => {
        fetch(`http://acit3855group45kafka.eastus2.cloudapp.azure.com:8100/stats`)
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP error status: ${res.status}`);
                }
                return res.json();
            })
            .then(
                (result) => {
                    console.log("Received Stats", result);
                    setStats(result);
                    setIsLoaded(true);
                },
                (error) => {
                    setError(error);
                    setIsLoaded(true);
                }
            );
    };

    useEffect(() => {
        const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return <div className={"error"}>Error found when fetching from API: {error.message}</div>;
    } else if (!isLoaded) {
        return <div>Loading...</div>;
    } else {
        return (
            <div>
                <h1>Latest Stats</h1>
                <table className={"StatsTable"}>
                    <tbody>
                        <tr>
                            <th>Card Events</th>
                            <th>Seller Rating Events</th>
                        </tr>
                        <tr>
                            <td># Card Events: {stats['num_card_events']}</td>
                            <td># Seller Rating Events: {stats['num_seller_rating_events']}</td>
                        </tr>
                        <tr>
                            <td>Max Card Price: {stats['max_card_price']}</td>
                            <td>Max Seller Rating: {stats['max_seller_rating']}</td>
                        </tr>
                            <td>Last Updated: {stats['last_updated']}</td>
                    </tbody>
                </table>
            </div>
        );
    }
}
