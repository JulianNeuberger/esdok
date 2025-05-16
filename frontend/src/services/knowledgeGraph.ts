import {Entity} from "./metaModelService";

export interface DataSource {
    file: string;
    pageStart: number;
    pageEnd: number;
}

export interface Node {
    id: string;
    name: string;
    entity: Entity;
    position: {x: number, y: number};
    source: DataSource;
}

export interface Edge {
    id: string;
    type: string;
    source: Node;
    target: Node;
}

export interface KnowledgeGraph {
    nodes: Node[];
    edges: Edge[];
}

export class KnowledgeGraphService {
    private backendHost = process.env.REACT_APP_BACKEND_HOST;

    public listGraphs = async (): Promise<string[]> => {
        const response = await fetch(`${this.backendHost}/graph/`);
        return response.json();
    }

    public load = async (metaModel: string): Promise<KnowledgeGraph | undefined> => {
        const response = await fetch(`${this.backendHost}/graph/${metaModel}/`, {
            method: "GET"
        });
        const json = await response.json();
        if(!Object.hasOwn(json, "nodes")) {
            return undefined;
        }
        if(!Object.hasOwn(json, "edges")) {
            return undefined;
        }
        return json;
    }

    public extract = async (file: File, metaModel: string): Promise<boolean> => {
        const data = new FormData();
        data.append("file", file);
        data.append("metaModel", metaModel);

        const response = await fetch(`${this.backendHost}/graph/extract/`, {
            method: "POST",
            body: data
        });

        const json = await response.json();
        return json["success"];
    }

    public layout = async (metaModel: string) => {
        const response = await fetch(`${this.backendHost}/graph/${metaModel}/layout/`, {
            method: "GET",
        });
        const json = await response.json();
        return json["success"];
    }

    public delete = async (metaModel: string) => {
        await fetch(`${this.backendHost}/graph/${metaModel}/`, {
            method: "DELETE"
        });
    }
}