import React from "react";
import {Button, Form, Input, Select} from "antd";
import {Aspect, Entity, Relation} from "../../services/metaModelService";
import TextArea from "antd/es/input/TextArea";


export interface Props {
    relation: Partial<Relation>;
    onChange: (e: Partial<Relation>) => void;
    onSubmit: (e: Relation) => void;
}

const RelationInput = ({relation, onChange, onSubmit}: Props) => {
    return (
        <Form>
            <Form.Item>New Relation</Form.Item>
            <Form.Item label={"name"}>
                <Input value={relation.name} onChange={(e) => {
                    onChange({
                        ...relation,
                        name: e.target.value
                    })
                }}/>
            </Form.Item>
            <Form.Item label={"description"}>
                <TextArea value={relation.description} onChange={(e) => {
                    onChange({
                        ...relation,
                        description: e.target.value
                    })
                }}/>
            </Form.Item>
            <Form.Item>
                <Button
                    type={"primary"}
                    onClick={() => {
                        if(!relation.description) return;
                        if(!relation.name) return;
                        onSubmit({
                            name: relation.name,
                            description: relation.description
                        });
                    }}
                >
                    Create
                </Button>
            </Form.Item>
        </Form>
    );
}

export default RelationInput;