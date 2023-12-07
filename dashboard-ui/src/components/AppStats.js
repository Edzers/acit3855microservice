import React, { useEffect, useState } from 'react';
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [status, setStatus] = useState({});
    const [error, setError] = useState(null);

    // Function to fetch the service statuses
    const getServiceStatus = () => {
        fetch('http://acit3855group45kafka.eastus2.cloudapp.azure.com:8120/health')
            .then(res => res.json())
            .then(
                (result) => {
                    setStatus(result);
                },
                (error) => {
                    setError(error);
                }
            );
    };

    // Function to fetch the stats
    const getStats = () => {
        fetch('http://acit3855group45kafka.eastus2.cloudapp.azure.com:8100/stats')
            .then(res => res.json())
            .then(
                (result) => {
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
        getStats();
        getServiceStatus();
        const statsInterval = setInterval(getStats, 2000); // Update stats every 2 seconds
        const statusInterval = setInterval(getServiceStatus, 20000); // Update service status every 20 seconds
        return () => {
            clearInterval(statsInterval);
            clearInterval(statusInterval);
        };
    }, []);

    // Function to format the last updated time
    const formatLastUpdate = () => {
        if (!status.last_update) return '...';
        const lastUpdateTime = new Date(status.last_update);
        const now = new Date();
        const secondsAgo = Math.round((now - lastUpdateTime) / 1000);
        return `${secondsAgo} seconds ago`;
    };

    if (error) {
        return <div className={"error"}>Error: {error.message}</div>;
    } else if (!isLoaded) {
        return <div>Loading...</div>;
    } else {
        return (
            <div>
                <h1>Latest Stats and Service Status</h1>
                <div>Receiver: {status.receiver}</div>
                <div>Storage: {status.storage}</div>
                <div>Processing: {status.processing}</div>
                <div>Audit: {status.audit}</div>
                <div>Last Update: {formatLastUpdate()}</div>
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
                    </tbody>
                </table>
            </div>
        );
    }
}
